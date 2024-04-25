import pytest
from clingo import Control
import os
from flask import current_app

from viasp.server.database import CallCenter
from viasp.asp.replayer import apply_multiple
from viasp.shared.io import model_to_json, TransformerTransport

from helper import Transformer

def test_calls_are_filtered_after_application(clingo_call_run_sample, app_context):
    db = CallCenter()
    db.extend(clingo_call_run_sample)
    assert len(db.get_all()) == 4, "There should be four unused calls before reconstruction."
    assert len(db.get_pending()) == 4, "There should be four unused calls before reconstruction."
    _ = apply_multiple(db.get_all())
    assert len(db.get_all()) == 4, "Get all should still return all of them after application."
    assert len(db.get_pending()) == 0, "The call objects should be marked as used after application."


def test_client_works(client):
    """Test if the test client is ok"""
    assert client.get("/healthcheck").status_code == 200


@pytest.fixture
def sample_control():
    ctl = Control(["0"])
    ctl.add("base", [], "a(1..3). {h(b(X))} :- a(X).")
    ctl.ground([("base", [])])
    return ctl


@pytest.fixture
def sample_models(sample_control):
    models = []
    with sample_control.solve(yield_=True) as handle:
        for m in handle:
            models.append(model_to_json(m))
    return models


def test_client_clear_removes_all(client, sample_models):
    client.post("control/models", json=sample_models)
    client.post("control/models/clear")
    r = client.get("control/models")
    assert r.status_code == 200
    assert len(r.json) == 0

def test_client_mark_models(client, sample_models):
    client.post("control/models/clear")
    r = client.post("control/models", json=sample_models)
    assert r.data == b'ok'
    r = client.get("control/models")
    assert r.status_code == 200
    data = r.json
    assert len(data) == len(sample_models)
    assert data == sample_models


def test_client_mark_single_model(client, sample_models):
    client.post("control/models/clear")
    sample_model = sample_models[0]
    r = client.post("control/models", json=sample_model)
    assert r.data == b'ok'
    r = client.get("control/models")
    assert r.status_code == 200
    data = r.json
    assert data == [sample_model]


def test_client_mark_models_duplicates_are_removed(client, sample_models):
    client.post("control/models/clear")
    duplicate_models = sample_models + sample_models[:-1]
    r = client.post("control/models", json=duplicate_models)
    assert r.data == b'ok'
    r = client.get("control/models")
    assert r.status_code == 200
    data = r.json
    assert len(data) == len(sample_models)
    assert data == sample_models



@pytest.mark.skip(reason="Transformer not registered bc of base exception?")
def test_client_add_transformer(client_with_a_graph):
    client, _, _, _ = client_with_a_graph
    serializable_transformer = TransformerTransport.merge(Transformer, "", str(os.path.abspath(__file__)))
    serialized = current_app.json.dumps(serializable_transformer)
    res = client.post("/control/add_transformer",
                        data=serialized,
                        headers={'Content-Type': 'application/json'})
    assert res.status_code == 200
