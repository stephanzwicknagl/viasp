import json
from typing import Collection

import requests
from .shared.defaults import DEFAULT_BACKEND_URL
from .shared.io import DataclassJSONEncoder
from .shared.model import ClingoMethodCall, StableModel, TransformerTransport
from .shared.interfaces import ViaspClient
from .shared.simple_logging import log, Level, error


def backend_is_running(url=DEFAULT_BACKEND_URL):
    try:
        r = requests.get(f"{url}/healthcheck")
        return r.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def dict_factory_that_supports_uuid(kv_pairs):
    return {k: v for k, v in kv_pairs}


class ClingoClient(ViaspClient):

    def __init__(self, **kwargs):
        if "viasp_backend_url" in kwargs:
            self.backend_url = kwargs["viasp_backend_url"]
        else:
            self.backend_url = DEFAULT_BACKEND_URL
        if not backend_is_running(self.backend_url):
            log(f"Backend is unavailable at ({self.backend_url})", Level.WARN)

    def is_available(self):
        return backend_is_running(self.backend_url)

    def register_function_call(self, name, sig, args, kwargs):
        serializable_call = ClingoMethodCall.merge(name, sig, args, kwargs)
        self._register_function_call(serializable_call)

    def _register_function_call(self, call: ClingoMethodCall):
        if backend_is_running(self.backend_url):
            serialized = json.dumps(call, cls=DataclassJSONEncoder)
            r = requests.post(f"{self.backend_url}/control/add_call",
                              data=serialized,
                              headers={'Content-Type': 'application/json'})
            if not r.ok:
                error(f"{r.status_code} {r.reason}")
        else:
            error(f"Backend is unavailable at ({self.backend_url})")

    def set_target_stable_model(self, stable_models: Collection[StableModel]):
        serialized = json.dumps(stable_models, cls=DataclassJSONEncoder)
        r = requests.post(f"{self.backend_url}/control/models",
                          data=serialized,
                          headers={'Content-Type': 'application/json'})
        if r.ok:
            log(f"Set models.")
        else:
            error(f"Setting models failed [{r.status_code}] ({r.reason})")

    def show(self):
        self._reconstruct()
        r = requests.post(f"{self.backend_url}/control/show")
        if r.ok:
            log(f"Drawing in progress.")
        else:
            error(f"Drawing failed [{r.status_code}] ({r.text})")

    def _reconstruct(self):
        r = requests.get(f"{self.backend_url}/control/reconstruct")
        if r.ok:
            log(f"Reconstructing in progress.")
        else:
            error(f"Reconstructing failed [{r.status_code}] ({r.text})")

    def relax_constraints(self, *args, **kwargs):
        log("No answer sets found. Switching to transformed visualization.")
        serialized = json.dumps({
            "args": args,
            "kwargs": kwargs
        },
                                cls=DataclassJSONEncoder)
        r = requests.post(f"{self.backend_url}/control/relax",
                          data=serialized,
                          headers={'Content-Type': 'application/json'})
        if r.ok:
            log(f"Successfully transformed program constraints.")
            return '\n'.join(r.json())
        else:
            error(
                f"Transforming constraints failed [{r.status_code}] ({r.text})"
            )
            return None

    def clingraph(self, viz_encoding, engine, graphviz_type):
        if type(viz_encoding) == str:
            with open(viz_encoding, 'r') as viz_encoding:
                prg = viz_encoding.read().splitlines()
        else:
            prg = viz_encoding.read().splitlines()
        prg = '\n'.join(prg)

        serialized = json.dumps(
            {
                "viz-encoding": prg,
                "engine": engine,
                "graphviz-type": graphviz_type
            },
            cls=DataclassJSONEncoder)

        r = requests.post(f"{self.backend_url}/control/clingraph",
                          data=serialized,
                          headers={'Content-Type': 'application/json'})
        if r.ok:
            log(f"Clingraph visualization in progress.")
        else:
            error(
                f"Clingraph visualization failed [{r.status_code}] ({r.text})"
            )

    def _register_transformer(self, transformer, imports, path):
        serializable_transformer = TransformerTransport.merge(
            transformer, imports, path)
        serialized = json.dumps(serializable_transformer,
                                cls=DataclassJSONEncoder)
        r = requests.post(f"{self.backend_url}/control/add_transformer",
                          data=serialized,
                          headers={'Content-Type': 'application/json'})
        if r.ok:
            log(f"Transformer registered.")
        else:
            error(
                f"Registering transformer failed [{r.status_code}] ({r.text})"
            )

    def register_warning(self, warning):
        serializable_warning = json.dumps([warning], cls=DataclassJSONEncoder)
        r = requests.post(f"{self.backend_url}/control/warnings",
                          data=serializable_warning,
                          headers={'Content-Type': 'application/json'})
        if not r.ok:
            error(f"Registering warning failed [{r.status_code}] ({r.text})")