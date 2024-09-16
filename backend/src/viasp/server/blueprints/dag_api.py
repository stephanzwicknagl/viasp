import os
from collections import defaultdict
from typing import Union, Collection, Dict, List, Iterable

import igraph
import networkx as nx
import numpy as np
from flask import Blueprint, current_app, request, jsonify, abort, Response, send_file, session
from clingo.ast import AST

from ...asp.reify import ProgramAnalyzer, reify_list
from ...asp.justify import build_graph
from ...shared.defaults import STATIC_PATH
from ...shared.model import Transformation, Node, Signature
from ...shared.util import get_start_node_from_graph, is_recursive, hash_from_sorted_transformations, pairwise
from ...asp.utils import register_adjacent_sorts
from ...shared.io import StableModel
from ..database import load_recursive_transformations_hashes, save_graph, get_graph, clear_graph, set_current_graph, get_current_graph_hash, get_current_sort, load_program, load_transformer, load_models, load_clingraph_names, save_sort, load_dependency_graph


bp = Blueprint("dag_api",
               __name__,
               template_folder='../templates',
               static_folder='../static/',
               static_url_path='/static')

def nx_to_igraph(nx_graph: nx.DiGraph):
    return igraph.Graph.Adjacency((np.array(nx.to_numpy_array(nx_graph))
                                   > 0).tolist())

def _get_graph():
    try:
        graph = get_graph()
    except ValueError:
        graph = generate_graph()
    return graph


def igraph_to_networkx_layout(i_layout, nx_map):
    nx_layout = {}
    for i, pos in enumerate(i_layout.coords):
        nx_layout[nx_map[i]] = pos
    return nx_layout


def make_node_positions(nx_graph: nx.DiGraph, i_graph: igraph.Graph):
    layout = i_graph.layout_reingold_tilford(root=[0])
    layout.rotate(180)
    nx_map = {i: node for i, node in enumerate(nx_graph.nodes())}
    pos = igraph_to_networkx_layout(layout, nx_map)
    return pos


def get_sort(nx_graph: nx.DiGraph):
    i_graph = nx_to_igraph(nx_graph)
    pos = make_node_positions(nx_graph, i_graph)
    return pos


def handle_request_for_children(
        transformation_hash: str,
        ids_only: bool) -> Collection[Union[Node, int]]:
    graph: nx.DiGraph = _get_graph()
    children = list()
    for u, v, d in graph.edges(data=True):
        edge: Transformation = d['transformation']
        if str(edge.hash) == transformation_hash:
            children.append(v)
    pos: Dict[Node, List[float]] = get_sort(graph)
    ordered_children = sorted(children, key=lambda node: pos[node][0])
    if ids_only:
        ordered_children = [node.uuid for node in ordered_children]
    return ordered_children


@bp.route("/graph/clear", methods=["DELETE"])
def clear_all():
    clear_graph()
    return "ok", 200


@bp.route("/graph/children/<transformation_hash>", methods=["GET"])
def get_children(transformation_hash):
    if request.method == "GET":
        ids_only = request.args.get("ids_only", default=False, type=bool)
        to_be_returned = handle_request_for_children(transformation_hash,
                                                     ids_only)
        return jsonify(to_be_returned)
    raise NotImplementedError


def get_src_tgt_mapping_from_graph(shown_recursive_ids=[],
                                   shown_clingraph=False):
    graph = _get_graph()

    to_be_added = []

    for source, target, edge in graph.edges(data=True):
        to_be_added.append({
            "src": source.uuid,
            "tgt": target.uuid,
            "transformation": edge["transformation"].hash,
            "style": "solid"
        })

    for recursive_uuid in shown_recursive_ids:
        # get recursion super-node from graph
        try:
            node = next(n for n in graph.nodes if n.uuid == recursive_uuid)
        except StopIteration:
            continue
        _, _, edge = next(e for e in graph.in_edges(node, data=True))
        for source, target in pairwise(node.recursive):
            to_be_added.append({
                "src": source.uuid,
                "tgt": target.uuid,
                "transformation": edge["transformation"].hash,
                "style": "solid"
            })
        # add connections to outer node
        to_be_added.append({
            "src": node.uuid,
            "tgt": node.recursive[0].uuid,
            "transformation": edge["transformation"].hash,
            "recursion": "in",
            "style": "solid"
        })
        if graph.out_degree(node) > 0:
            # only add connection out if there are more nodes / clingraph
            to_be_added.append({
                "src": node.recursive[-1].uuid,
                "tgt": node.uuid,
                "transformation": edge["transformation"].hash,
                "recursion": "out",
                "style": "solid"
            })

    if shown_clingraph:
        clingraph = load_clingraph_names()
        for src, tgt in list(zip(last_nodes_in_graph(graph), clingraph)):
            to_be_added.append({
                "src": src,
                "tgt": tgt,
                "transformation": "boxrow_container",
                "style": "dashed"
            })
    return to_be_added


def find_reason_by_uuid(symbolid, nodeid):
    node = find_node_by_uuid(nodeid)

    symbolstr = str(
        getattr(next(filter(lambda x: x.uuid == symbolid, node.diff)),
                "symbol", ""))
    reasonids = [
        getattr(r, "uuid", "") for r in node.reason.get(symbolstr, [])
    ]
    return reasonids


@bp.route("/graph/sorts", methods=["GET", "POST"])
def get_possible_transformation_orders():
    if request.method == "POST":
        if request.json is None:
            return jsonify({'error': 'Missing JSON in request'}), 400
        moved_transformation = request.json["moved_transformation"] if "moved_transformation" in request.json else {
            "old_index": -1,
            "new_index": -1,
        }
        
        sorted_program_rules = [t.rules for t in get_current_sort()]
        moved_item = sorted_program_rules.pop(moved_transformation["old_index"])
        sorted_program_rules.insert(moved_transformation["new_index"], moved_item)
        sorted_program_transformations = ProgramAnalyzer(dependency_graph=load_dependency_graph()).make_transformations_from_sorted_program(sorted_program_rules)
        hash = hash_from_sorted_transformations(sorted_program_transformations)
        save_sort(hash, sorted_program_transformations)
        register_adjacent_sorts(sorted_program_transformations, hash)
        try:
            set_current_graph(hash)
        except ValueError:
            generate_graph()
        return jsonify({"hash":hash})
    elif request.method == "GET":
        return jsonify(get_current_graph_hash())
    raise NotImplementedError


@bp.route("/graph/transformations", methods=["GET"])
def get_all_transformations():
    return jsonify(get_current_sort())


@bp.route("/graph/edges", methods=["GET", "POST"])
def get_edges():
    to_be_returned = []
    if request.method == "POST":
        if request.json is None:
            abort(Response("No json data provided.", 400))
        shown_recursive_ids = request.json[
            "shownRecursion"] if "shownRecursion" in request.json else []
        shown_clingraph = request.json[
            "usingClingraph"] if "usingClingraph" in request.json else False
        to_be_returned = get_src_tgt_mapping_from_graph(
            shown_recursive_ids, shown_clingraph)
    elif request.method == "GET":
        to_be_returned = get_src_tgt_mapping_from_graph()

    jsonified = jsonify(to_be_returned)
    return jsonified


@bp.route("/graph/transformation/<uuid>", methods=["GET"])
def get_rule(uuid):
    graph = _get_graph()
    for _, _, edge in graph.edges(data=True):
        transformation: Transformation = edge["transformation"]
        if str(transformation.id) == str(uuid):
            return jsonify(transformation)
    abort(404)


@bp.route("/graph/model/<uuid>", methods=["GET"])
def get_node(uuid):
    graph = _get_graph()
    for node in graph.nodes():
        if node.uuid == uuid:
            return jsonify(node)
    abort(400)


@bp.route("/graph/facts", methods=["GET"])
def get_facts():
    graph = _get_graph()
    facts = [get_start_node_from_graph(graph)]
    r = jsonify(facts)
    return r


@bp.route("/graph", methods=["POST", "GET", "DELETE"])
def entire_graph():
    if request.method == "POST":
        if request.json is None:
            return jsonify({'error': 'Missing JSON in request'}), 400
        data = request.json['data']
        data = nx.node_link_graph(data) if type(data) == dict else data
        hash = request.json['hash']
        sort = request.json['sort']
        sort = current_app.json.loads(sort) if type(sort) == str else sort
        save_graph(data, hash, sort)
        register_adjacent_sorts(sort, hash)
        _ = set_current_graph(hash)
        return jsonify({'message': 'ok'}), 200
    elif request.method == "GET":
        result = _get_graph()
        return jsonify(result)
    elif request.method == "DELETE":
        clear_graph()
        return jsonify({'message': 'ok'}), 200
    raise NotImplementedError


def get_atoms_in_path_by_signature(uuid: str):
    signature_to_atom_mapping = defaultdict(set)
    node = find_node_by_uuid(uuid)
    for s in node.atoms:
        signature = Signature(s.symbol.name, len(s.symbol.arguments))
        signature_to_atom_mapping[signature].add(s.symbol)
    return [(s, signature_to_atom_mapping[s])
            for s in signature_to_atom_mapping.keys()]


def find_node_by_uuid(uuid: str) -> Node:
    graph = _get_graph()
    matching_nodes = [x for x, _ in graph.nodes(data=True) if x.uuid == uuid]

    if len(matching_nodes) != 1:
        for node in graph.nodes():
            if len(node.recursive) > 0:
                matching_nodes = [
                    x for x in node.recursive
                    if x.uuid == uuid
                ]
                if len(matching_nodes) == 1:
                    return matching_nodes[0]
        abort(Response(f"No node with uuid {uuid}.", 404))
    return matching_nodes[0]


def get_kind(uuid: str) -> str:
    graph = _get_graph()
    node = find_node_by_uuid(uuid)
    recursive = is_recursive(node, graph)
    if recursive:
        return "Model"
    if len(graph.out_edges(node)) == 0:
        return "Answer Set"
    elif len(graph.in_edges(node)) == 0:
        return "Facts"
    else:
        return "Answer Set"


@bp.route("/detail/<uuid>")
def model(uuid):
    if uuid is None:
        abort(Response("Parameter 'key' required.", 400))
    kind = get_kind(uuid)
    path = get_atoms_in_path_by_signature(uuid)
    return jsonify((kind, path))


@bp.route("/detail/explain/<uuid>")
def explain(uuid):
    if uuid is None:
        abort(Response("Parameter 'key' required.", 400))
    node = find_node_by_uuid(uuid)
    explain = node.reason
    return jsonify(explain)


def get_all_signatures(graph: nx.Graph):
    signatures = set()
    for n in graph.nodes():
        for a in n.diff:
            signatures.add(Signature(a.symbol.name, len(a.symbol.arguments)))
    return signatures


@bp.route("/query", methods=["GET"])
def search():
    if "q" in request.args.keys():
        query = request.args["q"]
        graph = _get_graph()
        result = []
        signatures = get_all_signatures(graph)
        result.extend(signatures)
        for node in graph.nodes():
            if any(query in str(atm.symbol)
                   for atm in node.atoms) and node not in result:
                result.append(node)
        for _, _, edge in graph.edges(data=True):
            transformation = edge["transformation"]
            if any(query in rule for rule in
                   transformation.rules.str_) and transformation not in result:
                result.append(transformation)
        return jsonify(result[:10])
    return jsonify([])


@bp.route("/graph/clingraph/<uuid>", methods=["GET"])
def get_image(uuid):
    # check if file with name uuid exists in static folder
    filename = os.path.join("clingraph", f"{uuid}.png")
    file_path = os.path.join(STATIC_PATH, filename)
    if not os.path.isfile(file_path):
        return abort(Response(f"No clingraph with uuid {uuid}.", 404))
    return send_file(file_path, mimetype='image/png')


def last_nodes_in_graph(graph):
    return [n.uuid for n in graph.nodes() if graph.out_degree(n) == 0]


@bp.route("/clingraph/children", methods=["POST", "GET"])
def get_clingraph_children():
    if request.method == "GET":
        using_clingraph = load_clingraph_names()
        to_be_returned = [{
            "_type": "ClingraphNode",
            "uuid": c
        } for c in using_clingraph[::-1]]
        return jsonify(to_be_returned)
    raise NotImplementedError


@bp.route("/graph/reason", methods=["POST"])
def get_reasons_of():
    if request.method == "POST":
        if request.json is None:
            return jsonify({'error': 'Missing JSON in request'}), 400
        source_uuid = request.json["sourceid"]
        node_uuid = request.json["nodeid"]
        reason_uuids = find_reason_by_uuid(source_uuid, node_uuid)
        return jsonify([{
            "src": source_uuid,
            "tgt": reason_uuid
        } for reason_uuid in reason_uuids])
    raise NotImplementedError


def wrap_marked_models(
        marked_models: Iterable[StableModel],
        conflict_free_showTerm: str = "showTerm",
        clingraph: bool = False) -> List[List[str]]:
    result = []
    for model in marked_models:
        wrapped = []
        for part in model.atoms:
            wrapped.append(f"{part}.")
        for part in model.terms:
            if clingraph:
                wrapped.append(f"{part}.")
            else:
                wrapped.append(f"{conflict_free_showTerm}({part}).")
        result.append(wrapped)
    return result


def generate_graph() -> nx.DiGraph:
    analyzer = ProgramAnalyzer()
    analyzer.add_program(load_program(), load_transformer())

    marked_models = load_models()
    marked_models = wrap_marked_models(marked_models,
                                       analyzer.get_conflict_free_showTerm())
    if analyzer.will_work():
        recursion_rules = load_recursive_transformations_hashes()
        sorted_program = get_current_sort()
        reified: Collection[AST] = reify_list(
            sorted_program,
            h=analyzer.get_conflict_free_h(),
            h_showTerm=analyzer.get_conflict_free_h_showTerm(),
            model=analyzer.get_conflict_free_model(),
            conflict_free_showTerm=analyzer.get_conflict_free_showTerm(),
            get_conflict_free_variable=analyzer.get_conflict_free_variable,
            clear_temp_names=analyzer.clear_temp_names)
        g = build_graph(marked_models, reified, sorted_program, analyzer,
                        recursion_rules)
        save_graph(g, hash_from_sorted_transformations(sorted_program),
                   sorted_program)

    return g
