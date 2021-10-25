import pytest
from clingo import Control
from flask import Flask
from flask.testing import FlaskClient

from src.viasp.server.database import CallCenter
from src.viasp.asp.replayer import apply_multiple
from src.viasp.server.blueprints.api import bp as api_bp
from src.viasp.server.blueprints.app import bp as app_bp
from src.viasp.server.blueprints.dag_api import bp as dag_bp
from tests.pyt.test_replayer import run_sample
from src.viasp.shared.io import model_to_json


def test_calls_are_filtered_after_application():
    db = CallCenter()
    db.extend(run_sample())
    assert len(db.get_all()) == 4, "There should be four unused calls before reconstruction."
    assert len(db.get_pending()) == 4, "There should be four unused calls before reconstruction."
    _ = apply_multiple(db.get_all())
    assert len(db.get_all()) == 4, "Get all should still return all of them after application."
    assert len(db.get_pending()) == 0, "The call objects should be marked as used after application."


def create_app_with_registered_blueprints(*bps) -> Flask:
    app = Flask(__name__)
    for bp in bps:
        app.register_blueprint(bp)

    return app


@pytest.fixture
def client() -> FlaskClient:
    app = create_app_with_registered_blueprints(app_bp, api_bp, dag_bp)

    with app.test_client() as client:
        yield client


def test_client_works(client):
    """Test if the test client is ok"""
    assert client.get("/").status_code == 200


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


def test_client_mark_models(client, sample_models):
    r = client.post("control/models", json=sample_models)
    assert r.data == b'ok'
    r = client.get("control/models")
    assert r.status_code == 200
    data = r.json
    assert len(data) == len(sample_models)
    assert data == sample_models


def test_client_mark_single_model(client, sample_models):
    sample_model = sample_models[0]
    r = client.post("control/models", json=sample_model)
    assert r.data == b'ok'
    r = client.get("control/models")
    assert r.status_code == 200
    data = r.json
    assert data == sample_model


def test_client_clear_removes_all(client, sample_models):
    client.post("control/models", json=sample_models)
    client.post("control/models/clear")
    r = client.get("control/models")
    assert r.status_code == 200
    assert len(r.json) == 0


@pytest.mark.skip(reason="Not implemented yet")
def test_client_no_marked_model_uses_all_to_paint():
    pass


@pytest.mark.skip(reason="Not implemented yet")
def test_paint_with_stable_model_that_does_not_belong_to_models_throws():
    pass


@pytest.mark.skip(reason="Not implemented yet")
def test_querying_the_graph_without_calling_the_rerun_throws():
    pass
