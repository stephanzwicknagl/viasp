import io
import pathlib
import sys
from inspect import Signature
from typing import Sequence, Any, Dict, Collection

from flask.testing import FlaskClient

from viasp import wrapper
from viasp.shared.model import ClingoMethodCall, StableModel
from viasp.shared.interfaces import ViaspClient


def test_instanciations():
    _ = wrapper.Control()
    _ = wrapper.Control(["0"])


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

    def __init__(self, internal_client: FlaskClient):
        self.client = internal_client


def test_load_from_file(client):
    debug_client = DebugClient(client)
    ctl = wrapper.Control(_viasp_client=debug_client)
    sample_encoding = pathlib.Path(__file__).parent.resolve() / "resources" / "sample_encoding.lp"
    ctl.load(str(sample_encoding))
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


def test_load_from_stdin(client):
    debug_client = DebugClient(client)
    ctl = wrapper.Control(_viasp_client=debug_client)
    sys.stdin = io.StringIO("sample.{encoding} :- sample.")
    ctl.load("-")
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
    assert res.data == b"sample.{encoding} :- sample."
