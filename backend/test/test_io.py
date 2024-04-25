import networkx as nx
from networkx import node_link_data, node_link_graph
from flask import current_app

import clingo.ast
from clingo import Control, ModelType

from viasp.shared.io import clingo_model_to_stable_model
from viasp.shared.model import RuleContainer, StableModel, ClingoMethodCall, Signature, Transformation, TransformationError, \
    FailedReason
from viasp.server.database import get_database


def test_networkx_graph_with_dataclasses_is_isomorphic_after_dumping_and_loading_again(get_sort_program_and_get_graph):
    program = "c(1). c(2). b(X) :- c(X). a(X) :- b(X)."
    graph_info, _ = get_sort_program_and_get_graph(program)
    graph = graph_info[0]

    assert len(graph.nodes()) > 0, "The graph to check serialization should contain nodes."
    assert len(graph.edges()) > 0, "The graph to check serialization should contain edges."
    serializable_graph = node_link_data(graph)
    serialized_graph = current_app.json.dumps(serializable_graph)
    loaded = current_app.json.loads(serialized_graph)
    loaded_graph = node_link_graph(loaded)
    assert len(loaded_graph.nodes()) > 0, "The graph to check serialization should contain nodes."
    assert len(loaded_graph.edges()) > 0, "The graph to check serialization should contain edges."
    assert nx.is_isomorphic(loaded_graph,
                            graph), "Serializing and unserializing a networkx graph should not change it"


def test_serialization_model(app_context):
    ctl = Control(["0"])
    ctl.add("base", [], "{a(1..2)}. b(X) :- a(X).")

    ctl.ground([("base", [])])
    saved = []
    with ctl.solve(yield_=True) as h: # type: ignore
        for model in h:
            saved.append(clingo_model_to_stable_model(model))
    serialized = current_app.json.dumps(saved)
    deserialized = current_app.json.loads(serialized)
    for model in deserialized:
        assert isinstance(model, StableModel)


def test_serialization_calls(clingo_call_run_sample, app_context):
    serialized = current_app.json.dumps(clingo_call_run_sample)
    deserialized = current_app.json.loads(serialized)
    for model in deserialized:
        assert isinstance(model, ClingoMethodCall)


def test_failed_reason(app_context):
    object_to_serialize = FailedReason.FAILURE
    serialized = current_app.json.dumps(object_to_serialize)
    assert serialized

def test_rule_container(app_context):
    object_to_serialize = RuleContainer(str_=tuple(["test."]))
    serialized = current_app.json.dumps(object_to_serialize)
    assert serialized

def test_transformation(app_context):
    object_to_serialize = Transformation(1, RuleContainer(tuple()))
    serialized = current_app.json.dumps(object_to_serialize)
    assert serialized


def test_transformation_error(app_context):
    sample_data = []
    clingo.ast.parse_string("a.", lambda x: sample_data.append(x))
    object_to_serialize = TransformationError(sample_data[0], FailedReason.WARNING)
    serialized = current_app.json.dumps(object_to_serialize)
    assert serialized


def test_stable_model(app_context):
    object_to_serialize = StableModel([0], False, ModelType.StableModel, [], [], [], [])
    serialized = current_app.json.dumps(object_to_serialize)
    assert serialized


def test_signature(app_context):
    object_to_serialize = Signature("a", 1)
    serialized = current_app.json.dumps(object_to_serialize)
    assert serialized

def test_minimize_rule_representation(app_context):
    sort = [Transformation(0, RuleContainer(str_=tuple([":~ last(N). [N@0,1]"])))]
    db = get_database()
    sort_hash = "0"
    encoding_id = "1"
    db.save_sort(sort_hash, sort, encoding_id)
    db.set_current_graph(sort_hash, encoding_id)
    serialized = db.get_current_sort(encoding_id)
    assert serialized == sort



