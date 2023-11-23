import pytest

from viasp.shared.model import Node, Signature, Transformation
from viasp.shared.util import hash_from_sorted_transformations


@pytest.fixture(scope="function", autouse=True)
def reset_db(client):
    client.delete("graph/clear")


def test_query_endpoints_methods(client_with_a_graph):
    client, _, _, _ = client_with_a_graph
    res = client.get("query")
    assert res.status_code == 200
    res = client.post("query")
    assert res.status_code == 405
    res = client.delete("query")
    assert res.status_code == 405
    res = client.put("query")
    assert res.status_code == 405


def test_query_for_symbol(client_with_a_graph):
    client, _, _, program = client_with_a_graph
    q = "a(1)"
    res = client.get(f"query?q={q}")
    assert res.status_code == 200
    if "{b(X)}" in program:
        # program_simple and program_multiple_sorts
        assert any(any(str(atom.symbol) == q for atom in result.atoms) for result in res.json if isinstance(result, Node))
    else:
        # program_recursive
        assert all(all(str(atom.symbol) != q for atom in result.atoms) for result in res.json if isinstance(result, Node))


def test_query_for_signature(client_with_a_graph):
    client, _, _, program = client_with_a_graph
    q = "a/1"
    res = client.get(f"query?q={q}")
    assert res.status_code == 200
    if "{b(X)}" in program:
        # program_simple and program_multiple_sorts
        assert any(result.args == 1 and result.name == "a" for result in res.json if isinstance(result, Signature))
    else:
        # program_recursive
        assert all(result.args != 1 and result.name != "a" for result in res.json if isinstance(result, Signature))



def test_query_for_rule(client_with_a_graph):
    client, _, _, program = client_with_a_graph
    searched_rule = "{b(X)} :- a(X)."
    q = "b(X)"
    res = client.get(f"query?q={q}")
    print(res.json)
    assert res.status_code == 200
    if "{b(X)}" in program:
        # program_simple and program_multiple_sorts
        assert any(any(searched_rule in str(rule) for rule in result.rules) for result in res.json if
                isinstance(result, Transformation))
    else:
        # program_recursive
        assert all(all(searched_rule not in str(rule) for rule in result.rules) for result in res.json if
                isinstance(result, Transformation))


def test_query_multiple_sorts(client_with_a_graph):
    client, analyzer, serializable_graphs, program = client_with_a_graph
    _, _, _, length = serializable_graphs[0]
    results = []
    q = "c(X) :- a(X)."
    sorted_programs = analyzer.get_sorted_program()
    for _ in range(length):
        hash = hash_from_sorted_transformations(next(sorted_programs))
        res = client.post("graph/sorts", json={"hash": hash})
        assert res.status_code == 200
        res = client.get(f"query?q={q}")
        assert res.status_code == 200
        results.append(res.json)
    if length > 1:
        assert results[0] != results[1]