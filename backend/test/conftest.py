from inspect import signature
from typing import List, Generator, Any, Mapping, Tuple, Callable
from uuid import uuid4

import networkx as nx
import pytest
from clingo import Control
from flask import Flask
from flask.testing import FlaskClient

from helper import get_clingo_stable_models
from viasp.asp.justify import build_graph, save_model
from viasp.asp.reify import ProgramAnalyzer, reify_list
from viasp.server.blueprints.api import bp as api_bp, save_analyzer_values
from viasp.server.blueprints.app import bp as app_bp
from viasp.server.blueprints.dag_api import bp as dag_bp
from viasp.shared.io import DataclassJSONProvider
from viasp.shared.util import hash_from_sorted_transformations
from viasp.shared.model import ClingoMethodCall, Node, SymbolIdentifier, Transformation
from viasp.server.database import GraphAccessor, get_or_create_encoding_id
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
        encoding_id = "0"
        db = GraphAccessor()
        db.clear()
        db.add_to_program(program, encoding_id)
        analyzer = ProgramAnalyzer()
        analyzer.add_program(db.load_program(encoding_id))
        return analyzer
    return c

@pytest.fixture
def get_sort_program(load_analyzer) -> Callable[[str], Tuple[List[Transformation], ProgramAnalyzer]]:
    def c(program: str):
        analyzer = load_analyzer(program)
        return analyzer.get_sorted_program(), analyzer
    return c

@pytest.fixture
def get_sort_program_and_get_graph(get_sort_program, app_context) -> Callable[[str], Tuple[Tuple[nx.DiGraph, str, List[Transformation]], ProgramAnalyzer]]:
    def c(program: str):
        """
        Returning a Tuple containing 
            * the graph, 
            * the hash of the sorted program,
            * the sorted program as json string
            * the analyzer
        """
        sorted_program, analyzer = get_sort_program(program)
        db=GraphAccessor()
        save_analyzer_values(analyzer)

        saved_models = get_clingo_stable_models(program)
        db.set_models(saved_models, get_or_create_encoding_id())
        wrapped_stable_models = [list(save_model(saved_model)) for saved_model in saved_models]
        reified = reify_list(sorted_program)
        recursion_rules = analyzer.check_positive_recursion()
        g = build_graph(wrapped_stable_models, reified, sorted_program, analyzer, recursion_rules)
        return (g, hash_from_sorted_transformations(sorted_program), sorted_program), analyzer
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
def client_with_a_single_node_graph(get_sort_program_and_get_graph, a_1) -> Generator[Tuple[FlaskClient, ProgramAnalyzer, List[Tuple[nx.DiGraph, str, str, int]], str], Any, Any]:
    app = create_app_with_registered_blueprints(app_bp, api_bp, dag_bp)

    program = a_1
    graph_info, analyzer = get_sort_program_and_get_graph(program)
    with app.test_client() as client:
        graph_info, hash, sorted_program  = graph_info
        client.post("graph", json={"data": graph_info, "hash": hash, "sort": sorted_program})
        yield client, analyzer, graph_info, program


@pytest.fixture(params=["program_simple", "program_multiple_sorts", "program_recursive"])
def client_with_a_graph(
    request, get_sort_program_and_get_graph
) -> Generator[Tuple[FlaskClient, ProgramAnalyzer, Mapping, str], Any, Any]:
    app = create_app_with_registered_blueprints(app_bp, api_bp, dag_bp)

    program = request.getfixturevalue(request.param)
    (serializable_graph, hash, sorted_program), analyzer = get_sort_program_and_get_graph(
        program)
    with app.test_client() as client:
        client.post("graph",
                json={
                        "data": serializable_graph,
                        "hash": hash,
                        "sort": sorted_program
                    })
        yield client, analyzer, serializable_graph, program
        _ = client.delete("/control/clingraph")
        _ = client.post("/control/models/clear")
        _ = client.delete("/graph/clear")

@pytest.fixture
def client_with_a_clingraph(
    client_with_a_graph
) -> Generator[Tuple[FlaskClient, ProgramAnalyzer, Mapping, str], Any, Any]:
    client, analyzer, serializable_graph, program = client_with_a_graph

    serialized = get_clingo_stable_models(program)
    _ = client.post("/control/models",
                    json=serialized,
                    headers={'Content-Type': 'application/json'})

    yield client, analyzer, serializable_graph, program


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
