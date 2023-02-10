from viasp.api import (
        load_program_file,
        load_program_string,
        add_program_file,
        add_program_string,
        # unmark,
        # clear,
        # show,
        # relax_constraints,
        # clingraph
        )

import pathlib

from inspect import Signature, signature
from typing import Sequence, Any, Dict, Collection

from flask.testing import FlaskClient

from clingo import Control as InnerControl
from viasp.shared.model import ClingoMethodCall, StableModel
from viasp.shared.interfaces import ViaspClient


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
    sample_encoding = pathlib.Path(__file__).parent.resolve() / "resources" / "sample_encoding.lp"
    
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
    sample_encoding = pathlib.Path(__file__).parent.resolve() / "resources" / "sample_encoding.lp"
    
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
    sample_encoding = pathlib.Path(
        __file__).parent.resolve() / "resources" / "sample_encoding.lp"

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
    sample_encoding = pathlib.Path(
        __file__).parent.resolve() / "resources" / "sample_encoding.lp"

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
    sample_encoding = pathlib.Path(
        __file__).parent.resolve() / "resources" / "sample_encoding.lp"

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
