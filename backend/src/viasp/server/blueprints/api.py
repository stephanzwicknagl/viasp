from typing import Tuple, Any, Dict, Iterable, Collection, List
from unittest.mock import NonCallableMagicMock

from flask import request, Blueprint, jsonify, abort, Response, current_app
from flask_cors import cross_origin
from uuid import uuid4

from clingo import Control
from clingraph.orm import Factbase
from clingo.ast import AST
from clingraph.graphviz import compute_graphs, render
from ...shared.defaults import CLINGRAPH_PATH

from .dag_api import save_graph, last_nodes_in_graph, get_graph
from ..database import CallCenter, ProgramDatabase
from ...asp.justify import build_graph
from ...asp.reify import ProgramAnalyzer, reify_list
from ...asp.relax import ProgramRelaxer, relax_constraints
from ...shared.model import ClingoMethodCall, StableModel, Transformation
from ...shared.util import hash_from_sorted_transformations
from ...asp.replayer import apply_multiple

bp = Blueprint("api", __name__, template_folder='../templates/')

calls = CallCenter()
ctl = None
using_clingraph = []


def handle_call_received(call: ClingoMethodCall) -> None:
    global ctl
    calls.append(call)
    if ctl is not None:
        ctl = apply_multiple(calls.get_pending(), ctl)


def handle_calls_received(calls: Iterable[ClingoMethodCall]) -> None:
    for call in calls:
        handle_call_received(call)


@bp.route("/control/calls", methods=["GET"])
def get_calls():
    return jsonify(calls.get_all())


@bp.route("/control/program", methods=["GET"])
def get_program():
    db = ProgramDatabase()
    return db.get_program()
    

@bp.route("/control/add_call", methods=["POST"])
def add_call():
    if request.method == "POST":
        call = request.json
        if isinstance(call, ClingoMethodCall):
            handle_call_received(call)
        elif isinstance(call, list):
            handle_calls_received(call)
        else:
            abort(Response("Invalid call object", 400))
    return "ok", 200


def get_by_name_or_index_from_args_or_kwargs(name: str, index: int, *args: Tuple[Any], **kwargs: Dict[Any, Any]):
    if name in kwargs:
        return kwargs[name]
    elif index < len(args):
        return args[index]
    else:
        raise TypeError(f"No argument {name} found in kwargs or at index {index}.")


@bp.route("/control/reconstruct", methods=["GET"])
def reconstruct():
    if calls:
        global ctl
        ctl = apply_multiple(calls.get_pending(), ctl)
    return "ok"


class DataContainer:
    def __init__(self):
        self.models = []
        self.warnings = []
        self.transformer = None


dc = DataContainer()


def handle_models_received(parsed_models):
    dc.models = parsed_models


@bp.route("/control/models", methods=["GET", "POST"])
def set_stable_models():
    if request.method == "POST":
        try:
            parsed_models = request.json
        except BaseException:
            return "Invalid model object", 400
        handle_models_received(parsed_models)
    elif request.method == "GET":
        return jsonify(dc.models)
    return "ok"


@bp.route("/control/models/clear", methods=["POST"])
def models_clear():
    if request.method == "POST":
        dc.models.clear()
        global ctl
        ctl = None
    return "ok"


@bp.route("/control/add_transformer", methods=["POST"])
def set_transformer():
    if request.method == "POST":
        try:
            dc.transformer = request.json
        except BaseException:
            return "Invalid transformer object", 400
    return "ok", 200


def wrap_marked_models(marked_models: Iterable[StableModel]) -> List[List[str]]:
    result = []
    for model in marked_models:
        wrapped = []
        for part in model.atoms:
            wrapped.append(f"{part}.")
        result.append(wrapped)
    return result


def _set_warnings(warnings):
    dc.warnings = warnings

def used_clingraph():
    global using_clingraph
    return using_clingraph


@bp.route("/control/warnings", methods=["POST", "DELETE", "GET"])
def set_warnings():
    if request.method == "POST":
        _set_warnings(request.json)
    elif request.method == "DELETE":
        _set_warnings([])
    elif request.method == "GET":
        return jsonify(dc.warnings)
    return "ok"


@bp.route("/control/show", methods=["POST"])
def show_selected_models():
    marked_models: List[List[str]] = wrap_marked_models(dc.models)

    db = ProgramDatabase()
    analyzer = ProgramAnalyzer()
    analyzer.add_program(db.get_program(), dc.transformer)
    _set_warnings(analyzer.get_filtered())
    if analyzer.will_work():
        recursion_rules = analyzer.check_positive_recursion()
        for sorted_program in analyzer.get_sorted_program():
            reified: Collection[AST] = reify_list(sorted_program, 
                                h=analyzer.get_conflict_free_h(),
                                model=analyzer.get_conflict_free_model(),
                                get_conflict_free_variable=analyzer.get_conflict_free_variable)
            g = build_graph(marked_models, reified, sorted_program, analyzer, recursion_rules)
            save_graph(g, hash_from_sorted_transformations(sorted_program), current_app.json.dumps(sorted_program))
    return "ok", 200


@bp.route("/control/relax", methods=["POST"])
def transform_relax():
    db = ProgramDatabase()
    if request.json is None:
        return "Invalid request", 400
    args = request.json["args"] if "args" in request.json else []
    kwargs = request.json["kwargs"] if "kwargs" in request.json else {}
    relaxer = ProgramRelaxer(*args, **kwargs)
    relaxed = relax_constraints(relaxer, db.get_program())
    return jsonify(relaxed)


@bp.route("/control/clingraph", methods=["POST", "GET", "DELETE"])
def clingraph_generate():
    global using_clingraph

    if request.method == "POST":
        marked_models = dc.models
        marked_models = wrap_marked_models(marked_models)
        if request.json is None:
            return "Invalid request", 400
        viz_encoding = request.json["viz-encoding"] if "viz-encoding" in request.json else ""
        engine = request.json["engine"] if "engine" in request.json else "dot"
        graphviz_type = request.json["graphviz-type"] if "graphviz-type" in request.json else "digraph"


        # for every model that was maked
        for model in marked_models:
            # use clingraph to generate a graph
            control = Control()
            control.add("base", [], ''.join(model))
            control.add("base", [], viz_encoding)
            control.ground([("base", [])])
            with control.solve(yield_=True) as handle: # type: ignore
                for m in handle:
                    fb = Factbase.from_model(m, default_graph="base")
                    graphs = compute_graphs(fb, graphviz_type)

                    filename = uuid4().hex
                    if len(graphs) > 0:
                        render(graphs, format="png", directory=CLINGRAPH_PATH, name_format=filename, engine=engine)
                        using_clingraph.append(filename)
    if request.method == "GET":
        if len(using_clingraph) > 0:
            return jsonify({"using_clingraph": True}), 200
        return jsonify({"using_clingraph": False}), 200
    if request.method == "DELETE":
        using_clingraph = []
    return "ok", 200

def stringify_reified(reified: List[Collection[AST]]) -> str:
    ab = [", ".join(list(map(str,r))) for r in reified]
    st = '\n    '.join(ab)
    return st

