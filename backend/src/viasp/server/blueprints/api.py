from typing import Tuple, Any, Dict, Iterable

from flask import request, Blueprint, jsonify, abort, Response
from flask_cors import cross_origin

from .dag_api import set_graph
from ..database import CallCenter, ProgramDatabase
from ...asp.justify import build_graph
from ...asp.reify import ProgramAnalyzer, reify_list
from ...asp.relax import ProgramRelaxer
from ...shared.model import ClingoMethodCall, StableModel
from ...asp.replayer import apply_multiple

bp = Blueprint("api", __name__, template_folder='../templates/')

calls = CallCenter()
ctl = None


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


def wrap_marked_models(marked_models: Iterable[StableModel]):
    result = []
    for model in marked_models:
        wrapped = []
        for part in model.atoms:
            wrapped.append(f"model({part}).")
        result.append(wrapped)
    return result


def _set_warnings(warnings):
    dc.warnings = warnings


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
    analyzer.add_program(db.get_program())
    _set_warnings(analyzer.get_filtered())
    if analyzer.will_work():
        reified = reify_list(analyzer.get_sorted_program(), h=analyzer.get_conflict_free_h(),
                             model=analyzer.get_conflict_free_model())
        g = build_graph(marked_models, reified, analyzer)

        set_graph(g)
    return "ok", 200

@bp.route("/control/relax", methods=["POST"])
@cross_origin(origin='localhost', headers=['Content-Type', 'Authorization'])
def transform_relax():
    db = ProgramDatabase()
    relaxer = ProgramRelaxer(head_name="unsat", get_variables=True)
    relaxed = relaxer.relax_constraints(db.get_program())
    return jsonify(relaxed)


