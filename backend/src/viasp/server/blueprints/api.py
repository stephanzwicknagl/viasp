from typing import Tuple, Any, Dict, Iterable
from unittest.mock import NonCallableMagicMock

from flask import request, Blueprint, jsonify, abort, Response
from flask_cors import cross_origin
from uuid import uuid4

from clingo import Control
from clingraph.orm import Factbase
from clingraph.graphviz import compute_graphs, render
from ...shared.defaults import CLINGRAPH_PATH

from .dag_api import set_graph, last_nodes_in_graph, get_graph
from ..database import CallCenter, ProgramDatabase
from ...asp.justify import build_graph
from ...asp.reify import ProgramAnalyzer, reify_list
from ...asp.relax import ProgramRelaxer, relax_constraints
from ...shared.model import ClingoMethodCall, StableModel
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
    return "ok"


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

@bp.route("/control/add_transformer", methods=["POST"])
def set_transformer():
    if request.method == "POST":
        try:
            dc.transformer = request.json
        except BaseException:
            return "Invalid transformer object", 400
    return "ok"


def wrap_marked_models(marked_models: Iterable[StableModel]):
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


@bp.route("/control/warnings", methods=["POST"])
def set_warnings():
    _set_warnings(request.json)
    return "ok"


@bp.route("/control/warnings", methods=["DELETE"])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def clear_warnings():
    dc.warnings = []


@bp.route("/control/warnings", methods=["GET"])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def get_warnings():
    return jsonify(dc.warnings)


@bp.route("/control/show", methods=["POST"])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def show_selected_models():
    marked_models = dc.models
    marked_models = wrap_marked_models(marked_models)

    db = ProgramDatabase()
    analyzer = ProgramAnalyzer()
    analyzer.add_program(db.get_program(), dc.transformer)
    _set_warnings(analyzer.get_filtered())
    if analyzer.will_work():
        recursion_rules = analyzer.check_positive_recursion()
        reified = reify_list(analyzer.get_sorted_program(), h=analyzer.get_conflict_free_h(),
                             model=analyzer.get_conflict_free_model(),
                             get_conflict_free_variable=analyzer.get_conflict_free_variable)
        g = build_graph(marked_models, reified, analyzer, recursion_rules)

        set_graph(g)
    return "ok", 200

@bp.route("/control/relax", methods=["POST"])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def transform_relax():
    db = ProgramDatabase()
    relaxer = ProgramRelaxer(*request.json["args"], **request.json["kwargs"])
    relaxed = relax_constraints(relaxer, db.get_program())
    return jsonify(relaxed)

@bp.route("/control/clingraph", methods=["POST", "GET"])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def clingraph_generate():
    global using_clingraph

    if request.method == "POST":
        marked_models = dc.models
        marked_models = wrap_marked_models(marked_models)
        viz_encoding = request.json["viz-encoding"]
        engine = request.json["engine"]
        graphviz_type = request.json["graphviz-type"]


        # for every model that was maked
        for model in marked_models:
            # use clingraph to generate a graph
            control = Control()
            control.add("base", [], ''.join(model))
            control.add("base", [], viz_encoding)
            control.ground([("base", [])])
            with control.solve(yield_=True) as handle:
                for m in handle:
                    fb = Factbase.from_model(m, default_graph="base")
                    graphs = compute_graphs(fb, graphviz_type)

                    filename = uuid4().hex
                    using_clingraph.append(filename)
                    
                    render(graphs, format="png", directory=CLINGRAPH_PATH, name_format=filename, engine=engine)
    if request.method == "GET":
        if len(using_clingraph) > 0:
            return jsonify({"using_clingraph": True}), 200
        return jsonify({"using_clingraph": False}), 200
    return "ok", 200
