import json
import os
from collections import defaultdict
from typing import Union, Collection, Dict, List

import igraph
import networkx as nx
import numpy as np
from flask import Blueprint, request, jsonify, abort, Response, send_file
from flask_cors import cross_origin
from networkx import DiGraph

from ...shared.defaults import GRAPH_PATH, STATIC_PATH
from ...shared.io import DataclassJSONDecoder, DataclassJSONEncoder
from ...shared.model import Transformation, Node, Signature
from ...shared.util import get_start_node_from_graph, is_recursive

bp = Blueprint("dag_api", __name__, template_folder='../templates', static_folder='../static/',
               static_url_path='/static')

GRAPH = None


class GraphAccessor:

    def __init__(self):
        self.path = os.path.join(os.path.dirname(os.path.abspath(__file__)), GRAPH_PATH)

    def save(self, graph: Union[nx.Graph, dict]):
        if isinstance(graph, nx.Graph):
            serializable_graph = nx.node_link_data(graph)
        else:
            serializable_graph = graph
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(serializable_graph, f, cls=DataclassJSONEncoder, ensure_ascii=False, indent=2)

    def clear(self):
        self.save(nx.Graph())

    def load(self, as_json=True) -> Union[nx.DiGraph, dict]:
        try:
            with open(self.path, encoding="utf-8") as f:
                result = json.load(f, cls=DataclassJSONDecoder)
            if as_json:
                return result
            loaded_graph = nx.node_link_graph(result) if result is not None else nx.DiGraph()
            return loaded_graph
        except FileNotFoundError:
            return nx.DiGraph()


def get_database():
    return GraphAccessor()


def get_graph():
    global GRAPH
    if GRAPH is None:
        GRAPH = GraphAccessor().load(False)
    return GRAPH


def nx_to_igraph(nx_graph: DiGraph):
    return igraph.Graph.Adjacency((np.array(nx.to_numpy_array(nx_graph)) > 0).tolist()) # was nx.to_numpy_matrix(nx_graph) but will be deprecated in future


def igraph_to_networkx_layout(i_layout, nx_map):
    nx_layout = {}
    for i, pos in enumerate(i_layout.coords):
        nx_layout[nx_map[i]] = pos
    return nx_layout


def make_node_positions(nx_graph: DiGraph, i_graph: igraph.Graph):
    layout = i_graph.layout_reingold_tilford(root=[0])
    layout.rotate(180)
    nx_map = {i: node for i, node in enumerate(nx_graph.nodes())}
    pos = igraph_to_networkx_layout(layout, nx_map)
    return pos


def get_sort(nx_graph: DiGraph):
    i_graph = nx_to_igraph(nx_graph)
    pos = make_node_positions(nx_graph, i_graph)
    return pos


def handle_request_for_children(transformation_id, ids_only) -> Collection[Union[Node, int]]:
    graph = get_graph()
    children = list()
    for u, v, d in graph.edges(data=True):
        edge: Transformation = d['transformation']
        if str(edge.id) == transformation_id:
            children.append(v)
    pos: Dict[Node, List[float]] = get_sort(graph)
    ordered_children = sorted(children, key=lambda node: pos[node][0])
    if ids_only:
        ordered_children = [node.uuid for node in ordered_children]
    return ordered_children


@bp.route("/graph/clear", methods=["DELETE"])
def clear_graph():
    graph = get_graph()
    graph.clear()
    return "ok", 200


@bp.route("/graph/children/<transformation_id>", methods=["GET"])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def get_children(transformation_id):
    if request.method == "GET":
        ids_only = request.args["ids_only"] if "ids_only" in request.args else False
        to_be_returned = handle_request_for_children(transformation_id, ids_only)
        return jsonify(to_be_returned)
    raise NotImplementedError


def get_src_tgt_mapping_from_graph(shown_nodes_ids=None, shown_recursive_ids=[]):
    shown_nodes_ids = set(shown_nodes_ids) if shown_nodes_ids is not None else None

    graph = get_database().load(as_json=False)
    nodes = set(graph.nodes)
    to_be_deleted = set(existing for existing in nodes if shown_nodes_ids is not None and existing.uuid not in shown_nodes_ids)

    to_be_added = []
    for recursive_uuid in shown_recursive_ids:
        # get node from graph where node attribute uuid is uuid
        node = next(n for n in nodes if n.uuid == recursive_uuid)
        for source, target in node.recursive.edges:
            to_be_added.append((source, target))
    graph.add_edges_from(to_be_added)

    for node in to_be_deleted:
        for source, _, _ in graph.in_edges(node, data=True):
            for _, target, _ in graph.out_edges(node, data=True):
                graph.add_edge(source, target)
        graph.remove_node(node)
    return [{"src": src.uuid, "tgt": tgt.uuid} for src, tgt in graph.edges()]

def get_src_tgt_mapping_from_clingraph(ids=None):
    from .api import using_clingraph, last_nodes_in_graph
    last = last_nodes_in_graph(get_graph())
    imgs = using_clingraph
    return [{"src": src, "tgt": tgt} for src, tgt in list(zip(last, imgs))]


@bp.route("/graph/transformations", methods=["GET"])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def get_all_transformations():
    graph = get_graph()
    returning = []
    for u, v in graph.edges:
        transformation = graph[u][v]["transformation"]
        if transformation not in returning:
            returning.append(transformation)

    r = jsonify(returning)
    return r


@bp.route("/graph/edges", methods=["GET", "POST"])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def get_edges():
    to_be_returned = []
    if request.method == "POST":
        shown_recursive_ids = request.json["shownRecursion"] if "shownRecursion" in request.json else []
        to_be_returned = get_src_tgt_mapping_from_graph(request.json["shownNodes"], shown_recursive_ids)
    elif request.method == "GET":
        to_be_returned = get_src_tgt_mapping_from_graph()

    jsonified = jsonify(to_be_returned)
    return jsonified

@bp.route("/clingraph/edges", methods=["GET", "POST"])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def get_clingraph_edges():
    to_be_returned = []
    if request.method == "POST":
        to_be_returned = get_src_tgt_mapping_from_clingraph(request.json)
    elif request.method == "GET":
        to_be_returned = get_src_tgt_mapping_from_clingraph()
    jsonified = jsonify(to_be_returned)
    return jsonified


@bp.route("/graph/transformation/<uuid>", methods=["GET"])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def get_rule(uuid):
    graph = get_graph()
    for _, _, edge in graph.edges(data=True):
        transformation: Transformation = edge["transformation"]
        if str(transformation.id) == str(uuid):
            return jsonify(transformation)
    abort(404)


@bp.route("/graph/model/<uuid>", methods=["GET"])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def get_node(uuid):
    graph = get_graph()
    for node in graph.nodes():
        if node.uuid == uuid:
            return jsonify(node)
    abort(400)


@bp.route("/graph/facts", methods=["GET"])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def get_facts():
    graph = get_graph()
    facts = get_start_node_from_graph(graph)
    r = jsonify(facts)
    return r


@bp.route("/graph", methods=["POST", "GET", "DELETE"])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def entire_graph():
    if request.method == "POST":
        data = request.json
        set_graph(data)
        return "ok"
    elif request.method == "GET":
        result = get_graph()
        return jsonify(result)
    elif request.method == "DELETE":
        clear_graph()


def set_graph(data: DiGraph):
    database = get_database()
    database.save(data)
    global GRAPH
    GRAPH = None


def get_atoms_in_path_by_signature(uuid: str):
    signature_to_atom_mapping = defaultdict(set)
    node = find_node_by_uuid(uuid)
    for s in node.atoms:
        signature = Signature(s.symbol.name, len(s.symbol.arguments))
        signature_to_atom_mapping[signature].add(s.symbol)
    return [(s, signature_to_atom_mapping[s])
            for s in signature_to_atom_mapping.keys()]


def find_node_by_uuid(uuid: str) -> Node:
    graph = get_graph()
    matching_nodes = [x for x, y in graph.nodes(data=True) if x.uuid == uuid]

    if len(matching_nodes) != 1:
        for node in graph.nodes():
            if node.recursive is not False:
                matching_nodes = [x for x, y in node.recursive.nodes(data=True) if x.uuid == uuid]
                if len(matching_nodes) == 1:
                    return matching_nodes[0]
        abort(Response(f"No node with uuid {uuid}.", 404))
    return matching_nodes[0]


def get_kind(uuid: str) -> str:
    graph = get_graph()
    node = find_node_by_uuid(uuid)
    recursive = is_recursive(node, graph)
    facts = get_start_node_from_graph(graph)
    if recursive:
        return "Model"
    if len(graph.out_edges(node)) == 0:
        return "Stable Model"
    elif len(graph.in_edges(node)) == 0:
        return "Facts"
    else:
        return "Model"


@bp.route("/detail/<uuid>")
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def model(uuid):
    if uuid is None:
        abort(Response("Parameter 'key' required.", 400))
    kind = get_kind(uuid)
    path = get_atoms_in_path_by_signature(uuid)
    return jsonify((kind, path))

@bp.route("/detail/explain/<uuid>")
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
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
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def search():
    if "q" in request.args.keys():
        query = request.args["q"]
        graph = get_graph()
        result = []
        signatures = get_all_signatures(graph)
        result.extend(signatures)
        for node in graph.nodes():
            if any(query in str(atm.symbol) for atm in node.atoms) and node not in result:
                result.append(node)
        for _, _, edge in graph.edges(data=True):
            transformation = edge["transformation"]
            if any(query in r for r in transformation.rules) and transformation not in result:
                result.append(transformation)
        return jsonify(result[:10])
    return jsonify([])

@bp.route("/graph/clingraph/<uuid>", methods=["GET"])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def get_image(uuid):
    # check if file with name uuid exists in static folder
    filename = os.path.join("clingraph", f"{uuid}.png")
    file_path = os.path.join(STATIC_PATH, filename)
    if not os.path.isfile(file_path):
        return None
    return send_file(file_path, mimetype='image/png')

def last_nodes_in_graph(graph):
    return [n.uuid for n in graph.nodes() if graph.out_degree(n) == 0]

@bp.route("/clingraph/children/<transformation_id>", methods=["GET"])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def get_clingraph_children(transformation_id):
    if request.method == "GET":
        from .api import using_clingraph
        to_be_returned = using_clingraph[::-1]
        return jsonify(to_be_returned)
    raise NotImplementedError