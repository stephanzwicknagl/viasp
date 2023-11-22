import pytest

from viasp.shared.model import Node, Signature, Transformation
from viasp.shared.util import hash_from_sorted_transformations


@pytest.fixture(scope="function", autouse=True)
def reset_db(client):
    client.delete("graph/clear")


def test_query_endpoints_methods(client_with_a_graph):
    res = client_with_a_graph.get("query")
    assert res.status_code == 200
    res = client_with_a_graph.post("query")
    assert res.status_code == 405
    res = client_with_a_graph.delete("query")
    assert res.status_code == 405
    res = client_with_a_graph.put("query")
    assert res.status_code == 405


def test_query_for_symbol(client_with_a_graph):
    q = "a(1)"
    res = client_with_a_graph.get(f"query?q={q}")
    assert res.status_code == 200
    assert any(any(str(atom.symbol) == q for atom in result.atoms) for result in res.json if isinstance(result, Node))


def test_query_for_signature(client_with_a_graph):
    q = "a/1"
    res = client_with_a_graph.get(f"query?q={q}")
    assert res.status_code == 200
    assert any(result.args == 1 and result.name == "a" for result in res.json if isinstance(result, Signature))


def test_query_for_rule(client_with_a_graph):
    searched_rule = "{b(X)} :- a(X)."
    q = "b(X)"
    res = client_with_a_graph.get(f"query?q={q}")
    print(res.json)
    assert res.status_code == 200
    assert any(any(searched_rule in str(rule) for rule in result.rules) for result in res.json if
            isinstance(result, Transformation))

def test_query_multiple_sorts(client_with_a_graph, loaded_analyzer, serializable_graphs):
    _, _, _, length = serializable_graphs[0]
    results = []
    q = "c(X) :- a(X)."
    sorted_programs = loaded_analyzer.get_sorted_program()
    for _ in range(length):
        hash = hash_from_sorted_transformations(next(sorted_programs))
        res = client_with_a_graph.post("graph/sorts", json={"hash": hash})
        assert res.status_code == 200
        res = client_with_a_graph.get(f"query?q={q}")
        assert res.status_code == 200
        results.append(res.json)
    if length > 1:
        assert results[0] != results[1]