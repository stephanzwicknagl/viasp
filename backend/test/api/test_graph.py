import pytest
from networkx import node_link_data

from viasp.shared.model import Node, Transformation


@pytest.fixture(scope="function", autouse=True)
def reset_db(client):
    client.delete("graph/clear")


def test_clear_empty_graph(client_with_a_graph):
    client, _, _, _ = client_with_a_graph
    res = client.delete("graph/clear")
    assert res.status_code == 200


def test_children_allows_get_only(client_with_a_graph):
    client, analyzer, _, _ = client_with_a_graph
    for t in next(analyzer.get_sorted_program()):
        res = client.get(f"graph/children/{t.hash}?ids_only=True")
        assert res.status_code == 200
        assert len(res.json) > 0
        res = client.post(f"graph/children/{t.hash}?ids_only=True")
        assert res.status_code == 405
        res = client.delete(f"graph/children/{t.hash}?ids_only=True")
        assert res.status_code == 405
        res = client.put(f"graph/children/{t.hash}?ids_only=True")
        assert res.status_code == 405


def test_set_graph(client_with_a_graph):
    client, _, serializable_graphs, _ = client_with_a_graph
    for serializable_graph, hash, sorted_program, _ in serializable_graphs:
        req = {"data": serializable_graph, "hash": hash, "sort": sorted_program}
        client.delete("graph/clear")
        res = client.post("graph", json=req)
        assert res.status_code == 200
        res = client.get("graph")
        assert len(res.json) >= 0.


def test_graph_entries(client_with_a_graph):
    client, _, serializable_graphs, _ = client_with_a_graph
    _, _, _, length = serializable_graphs[0]
    res = client.get("graph/sorts")
    assert res.status_code == 200
    assert len(res.json) == length
    assert type(res.json[0]) == list
    assert type(res.json[0][0]) == list
    assert type(res.json[0][0][0]) == Transformation
    assert type(res.json[0][1]) == str


def test_get_node(client, single_node_graph):
    client.delete("graph/clear")
    uuid = list(single_node_graph.nodes)[0].uuid
    serializable_graph = node_link_data(single_node_graph)
    hash = "0123"
    res = client.post("graph", json={"data": serializable_graph, "hash": hash, "sort": ""})
    assert res.status_code == 200
    res = client.get(f"graph/model/{uuid.hex}")
    assert res.status_code == 200
    assert res.json.uuid == uuid.hex


def test_detail_endpoint_requires_key(client_with_a_graph):
    client, _, _, _ = client_with_a_graph
    res = client.get("detail/")
    assert res.status_code == 404


def test_detail_endpoint_returns_details_on_valid_uuid(client_with_a_single_node_graph):
    client, _, serializable_graphs, program = client_with_a_single_node_graph
    uuid = serializable_graphs[0][0]["nodes"][0]["id"].uuid
    res = client.get(f"detail/{uuid.hex}")
    assert res.status_code == 200
    assert program[:-1] in str(res.json[1][0][1][0])
    assert res.json[0] == "Stable Model"


def test_get_transformation(client_with_a_graph):
    client, _, _, _ = client_with_a_graph
    res = client.get(f"/graph/transformation/1")
    assert res.status_code == 200
    assert type(res.json) == Transformation


def test_get_facts(client_with_a_graph):
    client, _, _, _ = client_with_a_graph
    res = client.get(f"/graph/facts")
    assert res.status_code == 200
    assert type(res.json) == Node


def test_get_edges(client_with_a_graph):
    client, _, _, program = client_with_a_graph
    res = client.get(f"/graph/edges")
    assert res.status_code == 200
    assert type(res.json) == list
    uuids = [node.uuid for node in client.get(f"/graph").json]
    res = client.post(f"/graph/edges", json={"shownNodes": uuids, "shownRecursion": []})
    assert res.status_code == 200
    assert type(res.json) == list
    if "{b(X)}" in program:
        # program_simple and program_multiple_sorts
        assert len(res.json) == 8
    else:
        # program_recursive
        assert len(res.json) == 2
        res = client.post(f"/graph/edges", json={"shownNodes": uuids, "shownRecursion": [uuids[-1]]})
        assert res.status_code == 200
        assert type(res.json) == list
        assert len(res.json) == 4

def test_get_transformations(client_with_a_graph):
    client, _, _, _ = client_with_a_graph
    res = client.get(f"/graph/transformations")
    assert res.status_code == 200
    assert type(res.json) == list
    assert len(res.json) == 2
