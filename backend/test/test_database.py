from viasp.server.database import CallCenter, GraphAccessor
import pytest
import pathlib
from typing import Tuple
import networkx as nx

from helper import get_stable_models_for_program
from viasp.shared.util import hash_from_sorted_transformations
from viasp.asp.reify import reify_list
from viasp.asp.justify import build_graph
from viasp.shared.model import TransformerTransport
from viasp.exampleTransformer import Transformer as ExampleTransfomer


@pytest.fixture(
    params=["program_simple", "program_multiple_sorts", "program_recursive"])
def graph_info(request,
    get_sort_program_all_sorts, app_context
) -> Tuple[nx.DiGraph, str, str]:
    program = request.getfixturevalue(request.param)
    sorted_programs, analyzer = get_sort_program_all_sorts(program)
    sorted_program = sorted_programs[0]

    saved_models = get_stable_models_for_program(program)
    reified = reify_list(sorted_program)
    recursion_rules = analyzer.check_positive_recursion()
    g = build_graph(saved_models, reified, sorted_program, analyzer,
                    recursion_rules)
    return (g,
            hash_from_sorted_transformations(sorted_program),
            sorted_program)


def test_add_a_call_to_database(clingo_call_run_sample):
    db = CallCenter()
    assert len(db.calls) == 0, "Database should be empty initially."
    assert len(db.get_all()) == 0, "Database should be empty initially."
    assert len(db.get_pending()) == 0, "Database should be empty initially."
    db.extend(clingo_call_run_sample)
    assert len(db.calls) == 4, "Database should contain 4 after adding 4."
    assert len(db.get_all()) == 4, "Database should contain 4 after adding 4."
    assert len(db.get_pending()) == 4, "Database should contain 4 pending after adding 4 and not consuming them."
    db.mark_call_as_used(clingo_call_run_sample[0])
    assert len(db.calls) == 4, "Database should contain 4 after adding 4."
    assert len(db.get_all()) == 4, "Database should contain 4 after adding 4."
    assert len(db.get_pending()) == 3, "Database should contain 3 pending after adding 4 and consuming one."


def test_program_database():
    db = GraphAccessor()
    encoding_id = "test"
    program1 = "a. b:-a."
    program2 = "c."
    assert len(db.load_program(encoding_id)) == 0, "Database should be empty initially."
    db.save_program(program1, encoding_id)
    assert db.load_program(encoding_id) == program1
    db.add_to_program(program2, encoding_id)
    assert db.load_program(encoding_id) == program1 + program2
    db.clear_program(encoding_id)
    assert len(db.load_program(encoding_id)) == 0, "Database should be empty after clearing."

def test_models_database(client_with_a_graph, get_clingo_stable_models):
    db = GraphAccessor()
    encoding_id = "test"
    _, _, _, program = client_with_a_graph
    serialized = get_clingo_stable_models(program)
    assert len(db.load_models(encoding_id)) == 0, "Database should be empty initially."
    db.set_models(serialized, encoding_id)
    assert db.load_models(encoding_id) == serialized
    db.clear_models(encoding_id)
    assert len(db.load_models(encoding_id)) == 0, "Database should be empty after clearing."


def test_graph_json_database(graph_info):
    db = GraphAccessor()
    encoding_id = "test"

    with pytest.raises(ValueError):
        db.load_graph_json(graph_info[1], encoding_id)
    db.save_graph(graph_info[0], graph_info[1], graph_info[2], encoding_id)
    r = db.load_graph_json(graph_info[1], encoding_id)
    assert type(r) == str
    assert len(r) > 0


def test_graph_database(graph_info):
    db = GraphAccessor()
    encoding_id = "test"

    with pytest.raises(ValueError):
        db.load_graph(graph_info[1], encoding_id)
    db.save_graph(graph_info[0], graph_info[1], graph_info[2], encoding_id)
    r = db.load_graph(graph_info[1], encoding_id)
    assert type(r) == nx.DiGraph
    assert len(r) > 0


def test_current_graph_json_database(graph_info):
    db = GraphAccessor()
    encoding_id = "test"

    with pytest.raises(ValueError):
        db.load_current_graph_json(encoding_id)
    db.save_graph(graph_info[0], graph_info[1], graph_info[2], encoding_id)
    db.set_current_graph(graph_info[1], encoding_id)
    assert len(db.load_current_graph_json(encoding_id)) > 0


def test_current_graph_database(graph_info):
    db = GraphAccessor()
    encoding_id = "test"

    with pytest.raises(ValueError):
        db.load_current_graph(encoding_id)
    db.save_graph(graph_info[0], graph_info[1], graph_info[2], encoding_id)
    db.set_current_graph(graph_info[1], encoding_id)
    r = db.load_current_graph(encoding_id)
    assert len(r) > 1
    assert type(r) == nx.DiGraph

    # encoding_id = "test2"
    db.save_graph(graph_info[0], graph_info[1][:5], graph_info[2], encoding_id)
    db.set_current_graph(graph_info[1][:5], encoding_id)
    r = db.load_current_graph(encoding_id)
    assert len(r) > 1
    assert type(r) == nx.DiGraph



def test_sorts_database(get_sort_program_all_sorts, program_multiple_sorts):
    db = GraphAccessor()
    encoding_id = "test"
    program = program_multiple_sorts
    sorts, _ = get_sort_program_all_sorts(program)

    r = db.load_all_sorts(encoding_id)
    assert type(r) == list
    assert len(r) == 0
    db.save_many_sorts([(hash_from_sorted_transformations(sort), sort, encoding_id) for sort in sorts])
    r = db.load_all_sorts(encoding_id)
    assert len(r) == 2
    assert type(r) == list


def test_current_sort_database(graph_info):
    db = GraphAccessor()
    encoding_id = "test"

    r = db.load_all_sorts(encoding_id)
    assert type(r) == list
    assert len(r) == 0
    db.save_graph(graph_info[0], graph_info[1], graph_info[2], encoding_id)
    db.set_current_graph(graph_info[1], encoding_id)
    r = db.get_current_sort(encoding_id)
    assert len(r) == 2
    assert type(r) == list

def test_clingraph_database():
    db = GraphAccessor()
    encoding_id = "test"
    clingraph_names = ["test1", "test2"]

    r = db.load_all_clingraphs(encoding_id)
    assert type(r) == list
    assert len(r) == 0
    for n in clingraph_names:
        db.save_clingraph(n, encoding_id)
    r = db.load_all_clingraphs(encoding_id)
    assert type(r) == list
    assert len(r) == 2

    db.clear_clingraph(encoding_id)
    r = db.load_all_clingraphs(encoding_id)
    assert type(r) == list
    assert len(r) == 0


@pytest.mark.skip(reason="Transformer not registered bc of base exception?")
def test_transformer_database(app_context):
    db = GraphAccessor()

    encoding_id = "test"
    transformer = ExampleTransfomer()
    path = str(
        pathlib.Path(__file__).parent.parent.resolve() / "src" / "viasp" / "exampleTransformer.py")
    transformer_transport = TransformerTransport.merge(transformer, "", path)
    db.save_transformer(transformer_transport, encoding_id)
    r = db.load_transformer(encoding_id)
    assert type(r) == ExampleTransfomer
    assert r == transformer
