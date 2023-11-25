import json
import os
from collections import defaultdict
from typing import Union, Collection, Dict, List, Tuple

import igraph
import networkx as nx
import sqlite3
import numpy as np
from flask import Blueprint, request, jsonify, abort, Response, send_file, current_app, g
from flask_cors import cross_origin
from networkx import DiGraph

from ...shared.defaults import GRAPH_PATH, STATIC_PATH
from ...shared.model import Transformation, Node, Signature
from ...shared.util import get_start_node_from_graph, is_recursive

bp = Blueprint("dag_api", __name__, template_folder='../templates', static_folder='../static/',
               static_url_path='/static')

class GraphAccessor:

    def __init__(self):
        self.dbpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), GRAPH_PATH)
        self.conn = sqlite3.connect(self.dbpath)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS graphs (
                hash TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                sort BLOB NOT NULL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS current_graph (
                hash TEXT PRIMARY KEY,
                FOREIGN KEY(hash) REFERENCES graphs(hash)
            )
        """)

    def save(self, graph: Union[nx.Graph, dict], hash: str, sort: str = ""):
        if isinstance(graph, nx.Graph):
            serializable_graph = nx.node_link_data(graph)
        else:
            serializable_graph = graph

        self.cursor.execute("""
            INSERT OR REPLACE INTO graphs (hash, data, sort) VALUES (?, ?, ?)
        """, (hash,  current_app.json.dumps(serializable_graph), sort))

        if self.cursor.execute("SELECT COUNT(*) FROM current_graph").fetchone()[0] == 0:
            self.set_current_graph(hash)
        self.conn.commit()

    def clear(self):
        self.cursor.execute("""
            DELETE FROM graphs
        """)
        self.cursor.execute("""
            DELETE FROM current_graph
        """)
        self.conn.commit()

    def get_current_graph(self) -> str:
        self.cursor.execute("""
            SELECT hash FROM current_graph
        """)
        result = self.cursor.fetchone()
        return result[0] if result is not None else ""
    
    def set_current_graph(self, hash: str):
        self.cursor.execute("DELETE FROM current_graph")
        self.cursor.execute("INSERT INTO current_graph (hash) VALUES (?)", (hash,))
        self.conn.commit()
    
    def load_json(self) -> dict:
        hash = self.get_current_graph()

        self.cursor.execute("""
            SELECT data FROM graphs WHERE hash = ?
        """, (hash,))
        result = self.cursor.fetchone()

        return current_app.json.loads(result[0]) if result is not None else dict()

    def load(self) -> nx.DiGraph:
        graph_json = self.load_json()
        loaded_graph = nx.node_link_graph(graph_json) if len(graph_json) > 0 else nx.DiGraph()
        return loaded_graph

    def get_current_sort(self) -> str:
        hash = self.get_current_graph()
        self.cursor.execute("""
            SELECT sort FROM graphs WHERE hash = ?
        """, (hash,))
        result = self.cursor.fetchone()
        return current_app.json.loads(result[0]) if result is not None else ""

    def load_all_sorts(self) -> List[Tuple[List[Transformation], str]]:
        self.cursor.execute("""
            SELECT sort, hash FROM graphs
        """)
        result: List[Tuple[str, str]] = self.cursor.fetchall()
        loaded_sorts: List[Tuple[List[Transformation], str]] = [(current_app.json.loads(r[0]), r[1]) for r in result]
        index_of_current_sort: int = [s[1] for s in loaded_sorts].index(self.get_current_graph())
        loaded_sorts = loaded_sorts[index_of_current_sort:] + loaded_sorts[:index_of_current_sort]
        return loaded_sorts


def get_database():
    if 'graph_accessor' not in g:
        g.graph_accessor = GraphAccessor()
    return g.graph_accessor


def get_graph() -> DiGraph:
    return get_database().load()

def get_graph_json() -> dict:
    return get_database().load_json()

def get_all_sorts() -> List[Tuple[List[Transformation], str]]:
    return get_database().load_all_sorts()

def set_current_graph(hash: str):
    db = get_database()
    if db.get_current_graph() == hash:
        return
    db.set_current_graph(hash)

def clear_graph():
    get_database().clear()

def nx_to_igraph(nx_graph: DiGraph):
    return igraph.Graph.Adjacency((np.array(nx.to_numpy_array(nx_graph)) > 0).tolist())


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


def handle_request_for_children(transformation_hash: str, ids_only: bool) -> Collection[Union[Node, int]]:
    graph: nx.DiGraph = get_graph()
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
        to_be_returned = handle_request_for_children(transformation_hash, ids_only)
        return jsonify(to_be_returned)
    raise NotImplementedError


def get_src_tgt_mapping_from_graph(shown_nodes_ids=[], shown_recursive_ids=[]):
    shown_nodes_ids = set(shown_nodes_ids)

    graph = get_graph()
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


def find_reason_by_uuid(symbolid, nodeid):
    node = find_node_by_uuid(nodeid)

    symbolstr = str(getattr(next(filter(lambda x: x.uuid == symbolid, node.diff)), "symbol", ""))
    reasonids = [getattr(r, "uuid", "") for r in node.reason.get(symbolstr, [])]
    return reasonids


@bp.route("/graph/sorts", methods=["GET", "POST"])
def get_possible_transformation_orders():
    if request.method == "POST":
        if request.json is None:
            return jsonify({'error': 'Missing JSON in request'}), 400
        hash = request.json["hash"]
        set_current_graph(hash)
        return "ok", 200
    elif request.method == "GET":
        sorts = get_all_sorts()
        return jsonify(sorts)
    raise NotImplementedError


@bp.route("/graph/transformations", methods=["GET"])
def get_all_transformations():
    response = get_database().get_current_sort()
    return jsonify(response)


@bp.route("/graph/edges", methods=["GET", "POST"])
def get_edges():
    to_be_returned = []
    if request.method == "POST":
        if request.json is None:
            return jsonify({'error': 'Missing JSON in request'}), 400
        shown_nodes_ids = request.json["shownNodes"] if "shownNodes" in request.json else []
        shown_recursive_ids = request.json["shownRecursion"] if "shownRecursion" in request.json else []
        to_be_returned = get_src_tgt_mapping_from_graph(shown_nodes_ids, shown_recursive_ids)
    elif request.method == "GET":
        to_be_returned = get_src_tgt_mapping_from_graph()

    jsonified = jsonify(to_be_returned)
    return jsonified


@bp.route("/clingraph/edges", methods=["GET", "POST"])
def get_clingraph_edges():
    to_be_returned = []
    if request.method == "POST":
        if request.json is None:
            return jsonify({'error': 'Missing JSON in request'}), 400
        to_be_returned = get_src_tgt_mapping_from_clingraph(request.json)
    elif request.method == "GET":
        to_be_returned = get_src_tgt_mapping_from_clingraph()
    jsonified = jsonify(to_be_returned)
    return jsonified


@bp.route("/graph/transformation/<uuid>", methods=["GET"])
def get_rule(uuid):
    graph = get_graph()
    for _, _, edge in graph.edges(data=True):
        transformation: Transformation = edge["transformation"]
        if str(transformation.id) == str(uuid):
            return jsonify(transformation)
    abort(404)


@bp.route("/graph/model/<uuid>", methods=["GET"])
def get_node(uuid):
    graph = get_graph()
    for node in graph.nodes():
        if node.uuid == uuid:
            return jsonify(node)
    abort(400)


@bp.route("/graph/facts", methods=["GET"])
def get_facts():
    graph = get_graph()
    facts = get_start_node_from_graph(graph)
    r = jsonify(facts)
    return r


@bp.route("/graph", methods=["POST", "GET", "DELETE"])
def entire_graph():
    if request.method == "POST":
        if request.json is None:
            return jsonify({'error': 'Missing JSON in request'}), 400
        data = request.json['data']
        hash = request.json['hash']
        sort = request.json['sort']
        save_graph(data, hash, sort)
        return jsonify({'message': 'ok'}), 200
    elif request.method == "GET":
        result = get_graph()
        return jsonify(result)
    elif request.method == "DELETE":
        clear_graph()
        return jsonify({'message': 'ok'}), 200
    raise NotImplementedError


def save_graph(data: DiGraph, hash: str, sort: str):
    database = get_database()
    database.save(data, hash, sort)


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
    matching_nodes = [x for x, _ in graph.nodes(data=True) if x.uuid == uuid]

    if len(matching_nodes) != 1:
        for node in graph.nodes():
            if node.recursive is not False:
                matching_nodes = [x for x, _ in node.recursive.nodes(data=True) if x.uuid == uuid]
                if len(matching_nodes) == 1:
                    return matching_nodes[0]
        abort(Response(f"No node with uuid {uuid}.", 404))
    return matching_nodes[0]


def get_kind(uuid: str) -> str:
    graph = get_graph()
    node = find_node_by_uuid(uuid)
    recursive = is_recursive(node, graph)
    if recursive:
        return "Model"
    if len(graph.out_edges(node)) == 0:
        return "Stable Model"
    elif len(graph.in_edges(node)) == 0:
        return "Facts"
    else:
        return "Model"


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
        graph = get_graph()
        result = []
        signatures = get_all_signatures(graph)
        result.extend(signatures)
        for node in graph.nodes():
            if any(query in str(atm.symbol) for atm in node.atoms) and node not in result:
                result.append(node)
        for _, _, edge in graph.edges(data=True):
            transformation = edge["transformation"]
            if any(query in str(r) for r in transformation.rules) and transformation not in result:
                result.append(transformation)
        return jsonify(result[:10])
    return jsonify([])


@bp.route("/graph/clingraph/<uuid>", methods=["GET"])
def get_image(uuid):
    # check if file with name uuid exists in static folder
    filename = os.path.join("clingraph", f"{uuid}.png")
    file_path = os.path.join(STATIC_PATH, filename)
    if not os.path.isfile(file_path):
        return abort(Response(f"No clingraph with uuid {uuid}.",404))
    return send_file(file_path, mimetype='image/png')


def last_nodes_in_graph(graph):
    return [n.uuid for n in graph.nodes() if graph.out_degree(n) == 0]


@bp.route("/clingraph/children", methods=["POST", "GET"])
def get_clingraph_children():
    if request.method == "GET":
        from .api import using_clingraph
        to_be_returned = using_clingraph[::-1]
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
        return jsonify([{"src": source_uuid, "tgt": reason_uuid} for reason_uuid in reason_uuids])
    raise NotImplementedError