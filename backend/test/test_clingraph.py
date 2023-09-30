import io
import sys
import json
from inspect import Signature
from typing import Sequence, Any, Dict, Collection

from flask.testing import FlaskClient

from viasp import wrapper
from viasp.shared.model import ClingoMethodCall, StableModel
from viasp.shared.interfaces import ViaspClient
from viasp.shared.io import DataclassJSONEncoder



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


def test_load_from_stdin(client):
    debug_client = DebugClient(client)
    ctl = wrapper.Control(_viasp_client=debug_client)
    sys.stdin = io.StringIO("1{person(a);person(b)}1.person(c) :- person(a).person(d) :- person(b).")
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
    assert res.data == b"1{person(a);person(b)}1.person(c) :- person(a).person(d) :- person(b)."
    # Assert model are posted correctly
    stable_models = '[{"_type": "StableModel", "cost": [], "optimality_proven": false, "type": {"__enum__": "ModelType.StableModel"}, "atoms": [{"_type": "Function", "name": "person", "positive": true, "arguments": [{"_type": "Function", "name": "a", "positive": true, "arguments": []}]}, {"_type": "Function", "name": "person", "positive": true, "arguments": [{"_type": "Function", "name": "c", "positive": true, "arguments": []}]}], "terms": [], "shown": [{"_type": "Function", "name": "person", "positive": true, "arguments": [{"_type": "Function", "name": "a", "positive": true, "arguments": []}]}, {"_type": "Function", "name": "person", "positive": true, "arguments": [{"_type": "Function", "name": "c", "positive": true, "arguments": []}]}], "theory": []}, {"_type": "StableModel", "cost": [], "optimality_proven": false, "type": {"__enum__": "ModelType.StableModel"}, "atoms": [{"_type": "Function", "name": "person", "positive": true, "arguments": [{"_type": "Function", "name": "b", "positive": true, "arguments": []}]}, {"_type": "Function", "name": "person", "positive": true, "arguments": [{"_type": "Function", "name": "d", "positive": true, "arguments": []}]}], "terms": [], "shown": [{"_type": "Function", "name": "person", "positive": true, "arguments": [{"_type": "Function", "name": "b", "positive": true, "arguments": []}]}, {"_type": "Function", "name": "person", "positive": true, "arguments": [{"_type": "Function", "name": "d", "positive": true, "arguments": []}]}], "theory": []}]'
    res = client.post("/control/models", data=stable_models, headers={'Content-Type': 'application/json'})
    assert res.status_code == 200
    res = client.get("control/models")
    assert res.status_code == 200
    # Assert clingraph calls are posted correctly
    res = client.get("/control/clingraph")
    assert res.status_code == 200
    assert res.data == b'{"using_clingraph":false}\n'
    prg = "node(X):-person(X).attr(node,a,color,blue):-node(a).attr(node,b,color,red):-node(b).attr(node,c,color,blue):-node(c).attr(node,d,color,red):-node(d)."
    serialized = json.dumps({"viz-encoding":prg, "engine":"dot", "graphviz-type": "graph"}, cls=DataclassJSONEncoder)
    res = client.post("/control/clingraph", data=serialized, headers={'Content-Type': 'application/json'})
    assert res.status_code == 200
    assert res.data == b'ok'
    res = client.get("/control/clingraph")
    assert res.status_code == 200
    assert res.data == b'{"using_clingraph":true}\n'
    res = client.get("/clingraph/children/0")
    assert res.status_code == 200
    clingraph_uuids = json.loads(res.data)
    assert len(clingraph_uuids) == 2
    res = client.get(f"/graph/clingraph/{clingraph_uuids[0]}")
    assert res.status_code == 200
    assert res.content_type == 'image/png'
