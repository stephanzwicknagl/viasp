from inspect import signature
from typing import Dict, List
from uuid import uuid4

import networkx as nx
import pytest
from clingo import Control
from clingo.symbol import Function, Number
from flask import Flask
from flask.testing import FlaskClient
from networkx import node_link_data

from helper import get_stable_models_for_program
from viasp.asp.justify import build_graph
from viasp.asp.reify import ProgramAnalyzer, reify_list
from viasp.server.blueprints.api import bp as api_bp
from viasp.server.blueprints.app import bp as app_bp
from viasp.server.blueprints.dag_api import bp as dag_bp
from viasp.shared.io import DataclassJSONEncoder, DataclassJSONDecoder, clingo_model_to_stable_model
from viasp.shared.model import ClingoMethodCall, Node, StableModel, SymbolIdentifier
from viasp.server.database import ProgramDatabase
from viasp.shared.defaults import CLINGRAPH_PATH, GRAPH_PATH, PROGRAM_STORAGE_PATH, STDIN_TMP_STORAGE_PATH

def create_app_with_registered_blueprints(*bps) -> Flask:
    app = Flask(__name__)
    for bp in bps:
        app.register_blueprint(bp)

    app.json_encoder = DataclassJSONEncoder
    app.json_decoder = DataclassJSONDecoder

    return app


@pytest.fixture
def single_node_graph(a_1):
    g = nx.DiGraph()
    uuid = uuid4()
    g.add_node(Node(frozenset([SymbolIdentifier(a_1)]), 1, frozenset([SymbolIdentifier(a_1)]), uuid=uuid))
    return g


@pytest.fixture
def a_1() -> Function:
    # loc = Location(Position("str",1,1), Position("str",1,1))
    return Function("A", [Number(1)])


@pytest.fixture
def serializable_graph() -> Dict:
    program = "a(1..2). {b(X)} :- a(X). c(X) :- b(X)."
    db = ProgramDatabase()
    db.clear_program()
    db.add_to_program(program)
    analyzer = ProgramAnalyzer()
    analyzer.add_program(program)
    sorted_program = analyzer.get_sorted_program()
    saved_models = get_stable_models_for_program(program)
    reified = reify_list(sorted_program)

    g = build_graph(saved_models, reified, analyzer, set())

    serializable_graph = node_link_data(g)
    return serializable_graph


@pytest.fixture
def client_with_a_graph(serializable_graph) -> FlaskClient:
    app = create_app_with_registered_blueprints(app_bp, api_bp, dag_bp)

    with app.test_client() as client:
        client.post("graph", json=serializable_graph)
        yield client


@pytest.fixture
def client() -> FlaskClient:
    app = create_app_with_registered_blueprints(app_bp, api_bp, dag_bp)

    with app.test_client() as client:
        yield client


@pytest.fixture
def clingo_call_run_sample():
    signature_object = Control()
    return [
        ClingoMethodCall.merge("__init__", signature(signature_object.__init__), [["0"]], {}),
        ClingoMethodCall.merge("add", signature(signature_object.add), [],
                               {"name": "base", "parameters": [], "program": "a. {b}. c :- not b."}),
        ClingoMethodCall.merge("ground", signature(signature_object.ground), [[("base", [])]], {}),
        ClingoMethodCall.merge("solve", signature(signature_object.solve), [], {"yield_": True})
    ]


@pytest.fixture
def clingo_stable_models() -> List[StableModel]:
    ctl = Control(["0"])
    ctl.add("base", [], "{b;c}.")
    ctl.ground([("base", [])])
    models = []
    with ctl.solve(yield_=True) as h:
        for m in h:
            models.append(clingo_model_to_stable_model(m))
    return models


@pytest.fixture
def serializable_recursive_graph() -> Dict:
    program = "j(X, X+1) :- X=0..5.j(X,  Y) :- j(X,Z), j(Z,Y)."
    db = ProgramDatabase()
    db.clear_program()
    db.add_to_program(program)
    analyzer = ProgramAnalyzer()
    analyzer.add_program(program)
    recursion_rules = analyzer.check_positive_recursion()
    saved_models = get_stable_models_for_program(program)
    reified = reify_list(analyzer.get_sorted_program(), h=analyzer.get_conflict_free_h(),
                             model=analyzer.get_conflict_free_model())
    g = build_graph(saved_models, reified, analyzer, recursion_rules)

    serializable_recursive_graph = node_link_data(g)
    return serializable_recursive_graph


@pytest.fixture
def client_with_a_recursive_graph(serializable_recursive_graph) -> FlaskClient:
    app = create_app_with_registered_blueprints(app_bp, api_bp, dag_bp)

    with app.test_client() as client:
        client.post("graph", json=serializable_recursive_graph)
        yield client

@pytest.fixture(scope="session", autouse=True)
def cleanup(request):
    """Cleanup files once testing is finished."""
    def remove_test_dir():
        """ when quitting app, remove all files in the static/clingraph folder and auxiliary program files
        """
        import os
        import shutil
        if os.path.exists(CLINGRAPH_PATH):
            shutil.rmtree(CLINGRAPH_PATH)
        for file in [GRAPH_PATH, PROGRAM_STORAGE_PATH, STDIN_TMP_STORAGE_PATH]:
            if os.path.exists(file):
                os.remove(file)

    request.addfinalizer(remove_test_dir)
