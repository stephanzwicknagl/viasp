from flask import Flask
from viasp.shared.model import ClingoMethodCall
from viasp.shared.io import DataclassJSONProvider

app = Flask(__name__)
app.json = DataclassJSONProvider(app)

def create_empty_call() -> ClingoMethodCall:
    return ClingoMethodCall("", {})


def test_registering_valid_call_should_return_ok(client):
    valid = create_empty_call()
    rv = client.post("/control/add_call", data=app.json.dumps(valid),
                     headers={'Content-Type': 'application/json'})
    assert rv.status == "200 OK"
    assert rv.data.decode("utf-8") == "ok"


def test_registering_invalid_call_should_return_404(client):
    some_dict = {"data ": [], "weird": "weird"}
    rv = client.post("/control/add_call", data=some_dict, headers={'Content-Type': 'application/json'})
    assert rv.status == "400 BAD REQUEST"
