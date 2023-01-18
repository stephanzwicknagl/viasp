import pytest
from networkx import node_link_data

from viasp.shared.model import Node, Transformation


@pytest.fixture(scope="function", autouse=True)
def reset_db(client):
    client.delete("graph/clear")


def test_clear_empty_graph(client_with_a_graph):
    res = client_with_a_graph.delete("graph/clear")
    assert res.status_code == 200


def test_children_allows_get_only(client_with_a_graph):
    res = client_with_a_graph.get("graph/children/1?ids_only=True`")
    assert res.status_code == 200
    assert len(res.json) > 0
    res = client_with_a_graph.post("graph/children/1?ids_only=True")
    assert res.status_code == 405
    res = client_with_a_graph.delete("graph/children/1?ids_only=True")
    assert res.status_code == 405
    res = client_with_a_graph.put("graph/children/1?ids_only=True")
    assert res.status_code == 405


def test_set_graph(serializable_graph, client_with_a_graph):
    client_with_a_graph.delete("graph/clear")
    res = client_with_a_graph.post("graph", json=serializable_graph)
    assert res.status_code == 200

    res = client_with_a_graph.get("graph")
    assert len(res.json) >= 0


def test_get_node(client_with_a_graph, single_node_graph):
    client_with_a_graph.delete("graph/clear")
    uuid = list(single_node_graph.nodes)[0].uuid
    serializable_graph = node_link_data(single_node_graph)
    res = client_with_a_graph.post("graph", json=serializable_graph)
    assert res.status_code == 200
    res = client_with_a_graph.get(f"graph/model/{uuid.hex}")
    assert res.status_code == 200
    assert res.json.uuid == uuid.hex


def test_detail_endpoint_requires_key(client_with_a_graph):
    res = client_with_a_graph.get("detail/")
    assert res.status_code == 404


def test_detail_endpoint_returns_details_on_valid_uuid(client_with_a_graph, single_node_graph, a_1):
    client_with_a_graph.delete("graph/clear")
    uuid = list(single_node_graph.nodes)[0].uuid
    serializable_graph = node_link_data(single_node_graph)
    client_with_a_graph.post("graph", json=serializable_graph)
    res = client_with_a_graph.get(f"detail/{uuid.hex}")
    assert res.status_code == 200
    assert a_1 in res.json[1][0][1]
    assert res.json[0] == "Stable Model"


def test_get_transformation(client_with_a_graph):
    res = client_with_a_graph.get("/graph/transformation/1")
    assert res.status_code == 200
    assert type(res.json) == Transformation


def test_get_facts(client_with_a_graph):
    res = client_with_a_graph.get("/graph/facts")
    assert res.status_code == 200
    assert type(res.json) == Node

def test_get_edges(client_with_a_graph):
    res = client_with_a_graph.get("/graph/edges")
    assert res.status_code == 200
    assert type(res.json) == list
    uuids = [node.uuid for node in client_with_a_graph.get("/graph").json]
    res = client_with_a_graph.post("/graph/edges", json={"shownNodes": uuids, "shownRecursion": []})
    assert res.status_code == 200
    assert type(res.json) == list
    assert len(res.json) == 8


def test_get_edges_with_recursion(client_with_a_recursive_graph):
    res = client_with_a_recursive_graph.get("/graph/edges")
    assert res.status_code == 200
    assert type(res.json) == list
    uuids = [node.uuid for node in client_with_a_recursive_graph.get("/graph").json]
    res = client_with_a_recursive_graph.post("/graph/edges", json={"shownNodes": uuids, "shownRecursion": [uuids[-1]]})
    assert res.status_code == 200
    assert type(res.json) == list
    assert len(res.json) == 4