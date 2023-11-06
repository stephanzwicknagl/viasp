import json
import time

from viasp.shared.io import DataclassJSONEncoder, DataclassJSONDecoder
from viasp.shared.model import ClingoMethodCall


def test_add_call_endpoint(client, clingo_call_run_sample):
    bad_value = {"foo": "bar"}
    res = client.post("/control/add_call", json=bad_value)
    assert res.status_code == 400
    res = client.post("/control/add_call", json=clingo_call_run_sample)
    assert res.status_code == 200
    res = client.delete("/control/add_call")
    assert res.status_code == 405
    res = client.put("/control/add_call")
    assert res.status_code == 405


def test_reconstruct_endpoint(client, clingo_call_run_sample):
    res = client.post("/control/add_call", json=clingo_call_run_sample)
    assert res.status_code == 200
    res = client.get("/control/reconstruct")
    assert res.status_code == 200
    res = client.post("/control/reconstruct")
    assert res.status_code == 405
    res = client.delete("/control/reconstruct")
    assert res.status_code == 405
    res = client.put("/control/reconstruct")
    assert res.status_code == 405


def test_model_endpoint(client, clingo_stable_models):
    res = client.post("/control/models", json=clingo_stable_models)
    assert res.status_code == 200
    res = client.get("/control/models")
    assert len(res.json) > 0
    assert len(clingo_stable_models) == len(res.json)
    client.post("/control/models/clear")
    res = client.get("/control/models")
    assert len(res.json) == 0


def test_show_endpoint(client, clingo_stable_models):
    client.delete("/graph")
    res = client.get("/graph")
    assert len(list(res.json.nodes)) == 0
    client.post("/control/models", json=clingo_stable_models)
    res = client.post("/control/show")
    assert res.status_code == 200
    res = client.get("/graph")
    assert len(list(res.json.nodes)) > 0
