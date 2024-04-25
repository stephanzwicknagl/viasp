from clingo import Control

from viasp.shared.io import model_to_json


def test_clingo_model_is_serializable():
    ctl = Control()
    ctl.add("base", [], "a(1..3). {b(X)} :- a(X).")
    ctl.ground([("base", [])])
    serialized_models = []
    with ctl.solve(yield_=True) as handle:  # type: ignore
        for model in handle:
            serialized_models.append(model_to_json(model))
    assert serialized_models
