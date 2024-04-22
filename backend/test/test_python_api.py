import pathlib
from inspect import Signature, signature
from typing import Any, Collection, Dict, Sequence

from clingo import Control as InnerControl
from flask.testing import FlaskClient
from pytest import raises

from viasp.api import (FactParserError,
                       add_program_file, add_program_string,
                       clear, load_program_file, load_program_string,
                       mark_from_clingo_model, mark_from_file,
                       mark_from_string, show, unmark_from_clingo_model,
                       unmark_from_file, unmark_from_string)
from viasp.shared.interfaces import ViaspClient
from viasp.shared.model import ClingoMethodCall, StableModel
from viasp.shared.io import clingo_model_to_stable_model


class DebugClient(ViaspClient):
    def show(self):
        pass

    def set_target_stable_model(self, stable_models: Collection[StableModel]):
        self.client.post("control/models", json=stable_models)

    def register_function_call(self, name: str, sig: Signature, args: Sequence[Any], kwargs: Dict[str, Any]):
        serializable_call = ClingoMethodCall.merge(name, sig, args, kwargs)
        self.client.post("control/add_call", json=serializable_call)

    def is_available(self):
        return True

    def __init__(self, internal_client: FlaskClient, *args, **kwargs):
        self.client = internal_client
        self.register_function_call(
            "__init__", signature(InnerControl.__init__), args, kwargs)


def test_load_program_file(client):
    sample_encoding = str(pathlib.Path(__file__).parent.resolve() / "resources" / "sample_encoding.lp")
    
    debug_client = DebugClient(client)
    load_program_file(sample_encoding, _viasp_client=debug_client)
    
    # Check that the calls were received
    res = client.get("control/calls")
    assert res.status_code == 200
    assert len(res.json) > 0
    # Start the reconstructing
    res = client.get("control/reconstruct")
    assert res.status_code == 200
    # Assert program was called correctly
    res = client.get("control/program")
    assert res.status_code == 200
    assert res.data.replace(b"\n",b"") == b"sample.{encoding} :- sample.", f"{res.data} should be equal to sample.encoding :- sample."


def test_load_program_string(client):
    debug_client = DebugClient(client)
    load_program_string("sample.{encoding} :- sample.",_viasp_client=debug_client)

    # Check that the calls were received
    res = client.get("control/calls")
    assert res.status_code == 200
    assert len(res.json) > 0
    # Start the reconstructing
    res = client.get("control/reconstruct")
    assert res.status_code == 200
    # Assert program was called correctly
    res = client.get("control/program")
    assert res.status_code == 200
    assert res.data.replace(b"\n",b"") == b"sample.{encoding} :- sample."


def test_add_program_file_add1(client):
    sample_encoding = str(pathlib.Path(__file__).parent.resolve() / "resources" / "sample_encoding.lp")
    
    debug_client = DebugClient(client)
    load_program_file(sample_encoding, _viasp_client=debug_client)


    add_program_file(sample_encoding)
    
   # Check that the calls were received
    res = client.get("control/calls")
    assert res.status_code == 200
    assert len(res.json) > 0
    # Start the reconstructing
    res = client.get("control/reconstruct")
    assert res.status_code == 200
    # Assert program was called correctly
    res = client.get("control/program")
    assert res.status_code == 200
    assert res.data.replace(b"\n", b"") ==\
        b"sample.{encoding} :- sample.sample.{encoding} :- sample."


def test_add_program_file_add2(client):
    sample_encoding = str(pathlib.Path(
        __file__).parent.resolve() / "resources" / "sample_encoding.lp")

    debug_client = DebugClient(client)
    load_program_file(sample_encoding, _viasp_client=debug_client)

    add_program_file("base", [], sample_encoding)

    # Assert program was called correctly
    res = client.get("control/program")
    assert res.status_code == 200
    assert res.data.replace(b"\n", b"") ==\
        b"sample.{encoding} :- sample.sample.{encoding} :- sample."
    
    
    add_program_file("base", parameters=[], program=sample_encoding)
    # Assert program was called correctly
    res = client.get("control/program")
    assert res.status_code == 200
    print(res.data)
    assert res.data.replace(b"\n", b"") ==\
        b"sample.{encoding} :- sample.sample.{encoding} :- sample.sample.{encoding} :- sample."


def test_add_program_string_add1(client):
    sample_encoding = str(pathlib.Path(
        __file__).parent.resolve() / "resources" / "sample_encoding.lp")

    debug_client = DebugClient(client)
    load_program_file(sample_encoding, _viasp_client=debug_client)

    add_program_string("sample.{encoding} :- sample.")

   # Check that the calls were received
    res = client.get("control/calls")
    assert res.status_code == 200
    assert len(res.json) > 0
    # Start the reconstructing
    res = client.get("control/reconstruct")
    assert res.status_code == 200
    # Assert program was called correctly
    res = client.get("control/program")
    assert res.status_code == 200
    assert res.data.replace(b"\n", b"") ==\
        b"sample.{encoding} :- sample.sample.{encoding} :- sample."


def test_add_program_string_add2(client):
    sample_encoding = str(pathlib.Path(
        __file__).parent.resolve() / "resources" / "sample_encoding.lp")

    debug_client = DebugClient(client)
    load_program_file(sample_encoding, _viasp_client=debug_client)

    add_program_string("base", [], "sample.{encoding} :- sample.")

    # Assert program was called correctly
    res = client.get("control/program")
    assert res.status_code == 200
    assert res.data.replace(b"\n", b"") ==\
        b"sample.{encoding} :- sample.sample.{encoding} :- sample."

    add_program_string("base", parameters=[],
                       program="sample.{encoding} :- sample.")
    # Assert program was called correctly
    res = client.get("control/program")
    assert res.status_code == 200
    print(res.data)
    assert res.data.replace(b"\n", b"") ==\
        b"sample.{encoding} :- sample.sample.{encoding} :- sample.sample.{encoding} :- sample."

def test_mark_model_from_clingo_model(client):
    debug_client = DebugClient(client)

    load_program_string(r"sample.{encoding} :- sample.", _viasp_client=debug_client)

    ctl = InnerControl(['0'])
    ctl.add("base", [], r"sample.{encoding} :- sample.")
    ctl.ground([("base", [])])
    with ctl.solve(yield_=True) as handle:  # type: ignore
        for m in handle:
            mark_from_clingo_model(m)
    show()

    # Assert the models were received
    res = client.get("control/models")
    assert res.status_code == 200
    assert len(res.json) == 2


def test_mark_model_from_string(client):
    debug_client = DebugClient(client)

    load_program_string(
        r"sample.{encoding} :- sample.", _viasp_client=debug_client)

    clear()
    show()
    # Assert the models were cleared
    res = client.get("control/models")
    assert res.status_code == 200
    assert len(res.json) == 0

    mark_from_string("sample.encoding.")
    mark_from_string("sample.")
    show()

    # Assert the models were received
    res = client.get("control/models")
    assert res.status_code == 200
    assert len(res.json) == 2
    

def test_mark_model_not_a_fact_file(client):
    debug_client = DebugClient(client)

    load_program_string(
        r"sample.{encoding} :- sample.", _viasp_client=debug_client)

    sample_encoding = str(pathlib.Path(
        __file__).parent.resolve() / "resources" / "sample_encoding.lp")
    with raises(FactParserError) as exc_info:
        mark_from_file(sample_encoding)
    exception_raised = exc_info.value
    assert exception_raised.line == 1
    assert exception_raised.column == 8


def test_mark_model_from_file(client):
    debug_client = DebugClient(client)

    load_program_string(
        r"sample.{encoding} :- sample.", _viasp_client=debug_client)

    clear()
    sample_model = str(pathlib.Path(
        __file__).parent.resolve() / "resources" / "sample_model.lp")
    mark_from_file(sample_model)
    show()

    res = client.get("control/models")
    assert res.status_code == 200
    assert len(res.json) == 1


def test_unmark_model_from_clingo_model(client):
    debug_client = DebugClient(client)

    load_program_string(r"sample.{encoding} :- sample.", _viasp_client=debug_client)

    ctl = InnerControl(['0'])
    ctl.add("base", [], r"sample.{encoding} :- sample.")
    ctl.ground([("base", [])])
    last_model = None

    clear()
    with ctl.solve(yield_=True) as handle:  # type: ignore
        for m in handle:
            mark_from_clingo_model(m)
            last_model = clingo_model_to_stable_model(m)
    show()

    # Assert the models were received
    res = client.get("control/models")
    assert res.status_code == 200
    assert len(res.json) == 2

    if last_model is not None:
        unmark_from_clingo_model(last_model)
    show()
    res = client.get("control/models")
    assert res.status_code == 200
    assert len(res.json) == 1

def test_unmark_model_from_string(client):
    debug_client = DebugClient(client)

    load_program_string(
        r"sample.{encoding} :- sample.", _viasp_client=debug_client)

    clear()
    mark_from_string("sample.encoding.")
    mark_from_string("sample.")
    unmark_from_string("sample.encoding.")
    show()

    # Assert the models were received
    res = client.get("control/models")
    assert res.status_code == 200
    assert len(res.json) == 1


def test_unmark_model_from_file(client):
    debug_client = DebugClient(client)

    load_program_string(
        r"sample.{encoding} :- sample.", _viasp_client=debug_client)

    clear()
    sample_model = str(pathlib.Path(
        __file__).parent.resolve() / "resources" / "sample_model.lp")
    mark_from_file(sample_model)
    unmark_from_file(sample_model)
    show()

    res = client.get("control/models")
    assert res.status_code == 200
    assert len(res.json) == 0

def test_call_in_different_order(client):
    debug_client = DebugClient(client)
    sample_model = str(pathlib.Path(
        __file__).parent.resolve() / "resources" / "sample_model.lp")

    show(_viasp_client=debug_client)
    clear()
    mark_from_file(sample_model)
    show()
    load_program_string(
        r"sample.{encoding} :- sample.", _viasp_client=debug_client)

    show()
    res = client.get("control/models")
    assert res.status_code == 200
    assert len(res.json) == 1

def test_mix_methods(client):
    debug_client = DebugClient(client)
    sample_model = str(pathlib.Path(
        __file__).parent.resolve() / "resources" / "sample_model.lp")
    load_program_string(
        r"sample.{encoding} :- sample.", _viasp_client=debug_client)

    clear()
    mark_from_file(sample_model)
    show()
    mark_from_string("sample.")

    show()
    res = client.get("control/models")
    assert res.status_code == 200
    assert len(res.json) == 2

    unmark_from_string("sample.encoding.")
    show()
    res = client.get("control/models")
    assert res.status_code == 200
    assert len(res.json) == 1

def test_mix_methods2(client):
    debug_client = DebugClient(client)
    sample_encoding = str(pathlib.Path(
        __file__).parent.resolve() / "resources" / "sample_encoding.lp")
    clear(_viasp_client=debug_client)
    load_program_file(sample_encoding)
    ctl = InnerControl(['0'])
    ctl.add("base", [], r"sample.{encoding} :- sample.")
    ctl.ground([("base", [])])
    with ctl.solve(yield_=True) as handle:  # type: ignore
        for m in handle:
            mark_from_clingo_model(m)
    show()
    res = client.get("control/models")
    assert res.status_code == 200
    assert len(res.json) == 2

    unmark_from_string("sample.")
    show()
    res = client.get("control/models")
    assert res.status_code == 200
    assert len(res.json) == 1
