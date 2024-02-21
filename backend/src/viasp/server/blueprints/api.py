from multiprocessing import Value
from typing import Tuple, Any, Dict, Iterable, Optional, List

from flask import request, Blueprint, jsonify, abort, Response
from uuid import uuid4

from clingo import Control
from clingraph.orm import Factbase
from clingo.ast import Transformer
from clingraph.graphviz import compute_graphs, render

from .dag_api import generate_graph, set_current_graph, wrap_marked_models, \
        load_program, load_transformer, load_models, \
        load_clingraph_names
from ..database import CallCenter, get_database, set_models, clear_models, save_many_sorts, save_clingraph, clear_clingraph, save_transformer, save_warnings, clear_warnings, load_warnings
from ...asp.reify import ProgramAnalyzer
from ...asp.relax import ProgramRelaxer, relax_constraints
from ...shared.model import ClingoMethodCall, StableModel, TransformerTransport
from ...shared.util import hash_from_sorted_transformations, get_or_create_encoding_id
from ...shared.defaults import CLINGRAPH_PATH
from ...asp.replayer import apply_multiple

bp = Blueprint("api", __name__, template_folder='../templates/')

calls = CallCenter()
ctl: Optional[Control] = None
using_clingraph: List[str] = []


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
    return load_program()


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


def get_by_name_or_index_from_args_or_kwargs(name: str, index: int, *args:
                                             Tuple[Any], **kwargs: Dict[Any,
                                                                        Any]):
    if name in kwargs:
        return kwargs[name]
    elif index < len(args):
        return args[index]
    else:
        raise TypeError(
            f"No argument {name} found in kwargs or at index {index}.")


@bp.route("/control/reconstruct", methods=["GET"])
def reconstruct():
    if calls:
        global ctl
        ctl = apply_multiple(calls.get_pending(), ctl)
    return "ok"



@bp.route("/control/models", methods=["GET", "POST"])
def set_stable_models():
    if request.method == "POST":
        try:
            parsed_models = request.json
        except BaseException:
            return "Invalid model object", 400
        if isinstance(parsed_models, str):
            parsed_models = [parsed_models]
        if not isinstance(parsed_models, list):
            return "Expected a model or a list of models", 400
        parsed_models = [m for i,m in enumerate(parsed_models) if m not in parsed_models[:i]]
        set_models(parsed_models)
    elif request.method == "GET":
        return jsonify(load_models())
    return "ok"


@bp.route("/control/models/clear", methods=["POST"])
def models_clear():
    if request.method == "POST":
        clear_models()
        global ctl
        ctl = None
    return "ok"


@bp.route("/control/add_transformer", methods=["POST"])
def set_transformer():
    if request.method == "POST":
        try:
            transformer = request.json
            if not isinstance(transformer, TransformerTransport):
                return "Expected a transformer object", 400
        except BaseException:
            return "Invalid transformer object", 400
        save_transformer(transformer)
    return "ok", 200


def _set_warnings(warnings):
    encoding_id = get_or_create_encoding_id()
    get_database().save_warnings(warnings, encoding_id)


@bp.route("/control/warnings", methods=["POST", "DELETE", "GET"])
def set_warnings():
    if request.method == "POST":
        if not isinstance(request.json, list):
            return "Expected a list of warnings", 400
        save_warnings(request.json)
    elif request.method == "DELETE":
        clear_warnings()
    elif request.method == "GET":
        return jsonify(load_warnings())
    return "ok"

def save_all_sorts(analyzer: ProgramAnalyzer, batch_size: int = 1000):
    sorts = []
    for sorted_program in analyzer.get_sorted_program():
        sorts.append((hash_from_sorted_transformations(sorted_program),
                        sorted_program))
        if len(sorts) >= batch_size:
            save_many_sorts(sorts)
            sorts = []
    if sorts:
        save_many_sorts(sorts)


def set_primary_sort(analyzer: ProgramAnalyzer):
    primary_sort = analyzer.get_primary_sort()
    primary_hash = hash_from_sorted_transformations(primary_sort)
    try:
        _ = set_current_graph(primary_hash)
    except ValueError:
        generate_graph()


def save_analyzer_values(analyzer: ProgramAnalyzer):
    pass

@bp.route("/control/show", methods=["POST"])
def show_selected_models():
    analyzer = ProgramAnalyzer()
    analyzer.add_program(load_program(), load_transformer())
    _set_warnings(analyzer.get_filtered())

    marked_models = load_models()
    marked_models = wrap_marked_models(marked_models,
                                       analyzer.get_conflict_free_showTerm())
    if analyzer.will_work():
        save_all_sorts(analyzer, batch_size=1000)
        set_primary_sort(analyzer)
        save_analyzer_values(analyzer)

    return "ok", 200


@bp.route("/control/relax", methods=["POST"])
def transform_relax():
    if request.json is None:
        return "Invalid request", 400
    args = request.json["args"] if "args" in request.json else []
    kwargs = request.json["kwargs"] if "kwargs" in request.json else {}
    relaxer = ProgramRelaxer(*args, **kwargs)
    relaxed = relax_constraints(relaxer, load_program())
    return jsonify(relaxed)


@bp.route("/control/clingraph", methods=["POST", "GET", "DELETE"])
def clingraph_generate():
    if request.method == "POST":
        marked_models = load_models()
        marked_models = wrap_marked_models(marked_models)
        if request.json is None:
            return "Invalid request", 400
        viz_encoding = request.json[
            "viz-encoding"] if "viz-encoding" in request.json else ""
        engine = request.json["engine"] if "engine" in request.json else "dot"
        graphviz_type = request.json[
            "graphviz-type"] if "graphviz-type" in request.json else "digraph"

        # for every model that was maked
        for model in marked_models:
            # use clingraph to generate a graph
            control = Control()
            control.add("base", [], ''.join(model))
            control.add("base", [], viz_encoding)
            control.ground([("base", [])])
            with control.solve(yield_=True) as handle:  # type: ignore
                for m in handle:
                    fb = Factbase.from_model(m, default_graph="base")
                    graphs = compute_graphs(fb, graphviz_type)

                    filename = uuid4().hex
                    if len(graphs) > 0:
                        render(graphs,
                               format="png",
                               directory=CLINGRAPH_PATH,
                               name_format=filename,
                               engine=engine)
                        save_clingraph(filename)
    if request.method == "GET":
        if len(load_clingraph_names()) > 0:
            return jsonify({"using_clingraph": True}), 200
        return jsonify({"using_clingraph": False}), 200
    if request.method == "DELETE":
        clear_clingraph()
    return "ok", 200
