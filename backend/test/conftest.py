from inspect import signature
from typing import List, Generator, Any, Mapping, Tuple, Callable
from uuid import uuid4

import networkx as nx
import pytest
from clingo import Control
from clingo.symbol import Function, Number, Symbol
from flask import Flask, json
from flask.testing import FlaskClient
from networkx import node_link_data

from helper import get_stable_models_for_program
from viasp.asp.justify import build_graph
from viasp.asp.reify import ProgramAnalyzer, reify_list
from viasp.server.blueprints.api import bp as api_bp
from viasp.server.blueprints.app import bp as app_bp
from viasp.server.blueprints.dag_api import bp as dag_bp
from viasp.shared.io import DataclassJSONProvider, clingo_model_to_stable_model
from viasp.shared.util import hash_from_sorted_transformations
from viasp.shared.model import ClingoMethodCall, Node, StableModel, SymbolIdentifier, Transformation
from viasp.server.database import ProgramDatabase
from viasp.shared.defaults import CLINGRAPH_PATH, GRAPH_PATH, PROGRAM_STORAGE_PATH, STDIN_TMP_STORAGE_PATH

def create_app_with_registered_blueprints(*bps) -> Flask:
    app = Flask(__name__)
    for bp in bps:
        app.register_blueprint(bp)

    app.json = DataclassJSONProvider(app)
    return app


@pytest.fixture
def single_node_graph(a_1):
    g = nx.DiGraph()
    uuid = uuid4()
    g.add_node(Node(frozenset([SymbolIdentifier(a_1)]), 1, frozenset([SymbolIdentifier(a_1)]), uuid=uuid))
    return g


@pytest.fixture
def a_1() -> Symbol:
    # loc = Location(Position("str",1,1), Position("str",1,1))
    return Function("A", [Number(1)])

@pytest.fixture
def app():
    """Create an app context, so tests can use Flask features like current_app, g, etc."""
    app = create_app_with_registered_blueprints(app_bp, api_bp, dag_bp)
    with app.app_context():
        yield app


@pytest.fixture
def sort_program(app) -> Callable[[str], List[Transformation]]:
    def c(program: str):
        analyzer = ProgramAnalyzer()
        sorted_program = analyzer.sort_program(program)
        return sorted_program
    return c

@pytest.fixture
def sort_program_and_get_graph(app) -> Callable[[str], nx.DiGraph]:
    def c(program: str):
        analyzer = ProgramAnalyzer()
        sorted_program = analyzer.sort_program(program)
        saved_models = get_stable_models_for_program(program)
        reified = reify_list(sorted_program)
        recursion_rules = analyzer.check_positive_recursion()


        g = build_graph(saved_models, reified, sorted_program, analyzer, recursion_rules)
        return g
    return c


@pytest.fixture
def program_1() -> str:
    return "a(1..2). {b(X)} :- a(X). c(X) :- b(X)."

@pytest.fixture
def program_2() -> str:
    # has 2 possible sortings
    return "a(1..2). {b(X)} :- a(X). c(X) :- a(X)."

@pytest.fixture(params=["program_1", "program_2"])
def loaded_analyzer(request) -> ProgramAnalyzer:
    program = request.getfixturevalue(request.param)
    db = ProgramDatabase()
    db.clear_program()
    db.add_to_program(program)
    analyzer = ProgramAnalyzer()
    analyzer.add_program(db.get_program())
    return analyzer

@pytest.fixture # scope = session??
def serializable_graphs(program_1, loaded_analyzer) -> List[Tuple[Mapping, str, str, int]]:
    """
    Returning List of Tuples containing 
        * the graph, 
        * the hash of the sorted program,
        * the sorted program as json string
        * the number of possible sorts
    """
    serializable_graphs = []

    saved_models = get_stable_models_for_program(program_1)
    sorted_programs = list(loaded_analyzer.get_sorted_program())
    recursion_rules = loaded_analyzer.check_positive_recursion()
    for sorted_program in sorted_programs:
        reified = reify_list(sorted_program)
    
        g = build_graph(saved_models, reified, sorted_program, loaded_analyzer, recursion_rules)

        serializable_graphs.append((node_link_data(g), hash_from_sorted_transformations(sorted_program), json.dumps(sorted_program), len(sorted_programs)))
    return serializable_graphs


@pytest.fixture
def client_with_a_graph(serializable_graphs) -> Generator[FlaskClient, Any, Any]:
    app = create_app_with_registered_blueprints(app_bp, api_bp, dag_bp)

    with app.test_client() as client:
        for serializable_graph, hash, sorted_program, _ in serializable_graphs:
            client.post("graph", json={"data": serializable_graph, "hash": hash, "sort": sorted_program})
        yield client


@pytest.fixture
def client() -> Generator[FlaskClient, Any, Any]:
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
    program = "{b;c}."
    return get_stable_models_for_program(program)


@pytest.fixture
def serializable_recursive_graphs() -> List[Mapping]:
    serializable_recursive_graphs = []
    program = "j(X, X+1) :- X=0..5.j(X,  Y) :- j(X,Z), j(Z,Y)."
    db = ProgramDatabase()
    db.clear_program()
    db.add_to_program(program)
    analyzer = ProgramAnalyzer()
    analyzer.add_program(program)
    recursion_rules = analyzer.check_positive_recursion()
    saved_models = get_stable_models_for_program(program)
    for sorted_program in analyzer.get_sorted_program():
        reified = reify_list(sorted_program)
    
        g = build_graph(saved_models, reified, sorted_program, analyzer, recursion_rules)

        serializable_recursive_graphs.append((node_link_data(g), hash_from_sorted_transformations(sorted_program), json.dumps(sorted_program)))
    return serializable_recursive_graphs


@pytest.fixture
def client_with_a_recursive_graph(serializable_recursive_graphs) -> Generator[FlaskClient, Any, Any]:
    app = create_app_with_registered_blueprints(app_bp, api_bp, dag_bp)

    with app.test_client() as client:
        for serializable_recursive_graph, hash, sorted_program in serializable_recursive_graphs:
            client.post("graph", json={"data": serializable_recursive_graph, "hash": hash, "sort": sorted_program})
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
