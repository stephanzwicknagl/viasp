from inspect import signature
from typing import List, Generator, Any, Mapping, Tuple, Callable
from uuid import uuid4

import networkx as nx
import pytest
from clingo import Control
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
def a_1() -> str:
    return "a(1)."

@pytest.fixture
def app_context():
    """Create an app context, so tests can use Flask features like current_app, g, etc."""
    app = create_app_with_registered_blueprints(app_bp, api_bp, dag_bp)

    with app.app_context():
        yield app

@pytest.fixture
def load_analyzer(app_context) -> Callable[[str], ProgramAnalyzer]:
    def c(program: str) -> ProgramAnalyzer:
        db = ProgramDatabase()
        db.clear_program()
        db.add_to_program(program)
        analyzer = ProgramAnalyzer()
        analyzer.add_program(db.get_program())
        return analyzer
    return c

@pytest.fixture
def get_sort_program(load_analyzer) -> Callable[[str], Tuple[List[Transformation], ProgramAnalyzer]]:
    def c(program: str):
        analyzer = load_analyzer(program)
        return next(analyzer.get_sorted_program()), analyzer
    return c

@pytest.fixture
def get_sort_program_all_sorts(load_analyzer) -> Callable[[str], Tuple[List[List[Transformation]], ProgramAnalyzer]]:
    def c(program: str):
        analyzer = load_analyzer(program)
        return list(analyzer.get_sorted_program()), analyzer
    return c

@pytest.fixture
def get_sort_program_and_get_graph(get_sort_program_all_sorts) -> Callable[[str], Tuple[Tuple[Mapping, str, str, int], ProgramAnalyzer]]:
    def c(program: str):
        """
        Returning a Tuple containing 
            * the graph, 
            * the hash of the sorted program,
            * the sorted program as json string
            * the number of possible sorts
        """
        sorted_programs, analyzer = get_sort_program_all_sorts(program)
        sorted_program =sorted_programs[0]

        saved_models = get_stable_models_for_program(program)
        reified = reify_list(sorted_program)
        recursion_rules = analyzer.check_positive_recursion()
        g = build_graph(saved_models, reified, sorted_program, analyzer, recursion_rules)
        return (node_link_data(g), hash_from_sorted_transformations(sorted_program), json.dumps(sorted_program), len(sorted_programs)), analyzer
    return c

@pytest.fixture
def get_sort_program_and_get_all_graphs(get_sort_program_all_sorts) -> Callable[[str], Tuple[List[Tuple[Mapping, str, str, int]], ProgramAnalyzer]]:
    def c(program: str):
        """
        Returning List of Tuples containing 
            * the graph, 
            * the hash of the sorted program,
            * the sorted program as json string
            * the number of possible sorts
        """
        serializable_graphs = []
        sorted_programs, analyzer = get_sort_program_all_sorts(program)


        saved_models = get_stable_models_for_program(program)
        recursion_rules = analyzer.check_positive_recursion()
        for sorted_program in sorted_programs:
            reified = reify_list(sorted_program)
            g = build_graph(saved_models, reified, sorted_program, analyzer, recursion_rules)
            serializable_graphs.append((node_link_data(g), hash_from_sorted_transformations(sorted_program), json.dumps(sorted_program), len(sorted_programs)))

        return serializable_graphs, analyzer
    return c


@pytest.fixture
def program_simple() -> str:
    return "a(1..2). {b(X)} :- a(X). c(X) :- b(X)."

@pytest.fixture
def program_multiple_sorts() -> str:
    return "a(1..2). {b(X)} :- a(X). c(X) :- a(X)."

@pytest.fixture
def program_recursive() -> str:
    return "j(X, X+1) :- X=0..5.j(X,  Y) :- j(X,Z), j(Z,Y)."


@pytest.fixture
def client_with_a_single_node_graph(get_sort_program_and_get_all_graphs, a_1) -> Generator[Tuple[FlaskClient, ProgramAnalyzer, List[Tuple[Mapping, str, str, int]], str], Any, Any]:
    app = create_app_with_registered_blueprints(app_bp, api_bp, dag_bp)
    
    program = a_1
    serializable_graphs, analyzer = get_sort_program_and_get_all_graphs(program)
    with app.test_client() as client:
        for serializable_graph, hash, sorted_program, _ in serializable_graphs:
            client.post("graph", json={"data": serializable_graph, "hash": hash, "sort": sorted_program})
        yield client, analyzer, serializable_graphs, program


@pytest.fixture(params=["program_simple", "program_multiple_sorts", "program_recursive"])
def client_with_a_graph(request, get_sort_program_and_get_all_graphs) -> Generator[Tuple[FlaskClient, ProgramAnalyzer, List[Tuple[Mapping, str, str, int]], str], Any, Any]:
    app = create_app_with_registered_blueprints(app_bp, api_bp, dag_bp)
    
    program = request.getfixturevalue(request.param)
    serializable_graphs, analyzer = get_sort_program_and_get_all_graphs(program)
    with app.test_client() as client:
        for serializable_graph, hash, sorted_program, _ in serializable_graphs:
            client.post("graph", json={"data": serializable_graph, "hash": hash, "sort": sorted_program})
        yield client, analyzer, serializable_graphs, program

@pytest.fixture
def client_with_a_clingraph(client_with_a_graph, get_clingo_stable_models) -> Generator[Tuple[FlaskClient, ProgramAnalyzer, List[Tuple[Mapping, str, str, int]], str], Any, Any]:
    client, analyzer, serializable_graphs, program = client_with_a_graph

    _ = client.delete("/control/clingraph")
    serialized = get_clingo_stable_models(program)
    _ = client.post("/control/models", json=serialized, headers={'Content-Type': 'application/json'})

    yield client, analyzer, serializable_graphs, program


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
def get_clingo_stable_models() -> Callable[[str], List[StableModel]]:
    def c(program: str) -> List[StableModel]:
        wrapped_models = []

        ctl = Control(["0"])
        ctl.add("base", [], program)
        ctl.ground([("base", [])])
        with ctl.solve(yield_=True) as handle: # type: ignore
            for model in handle: 
                wrapped_models.append(clingo_model_to_stable_model(model))
        return wrapped_models
    return c

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
