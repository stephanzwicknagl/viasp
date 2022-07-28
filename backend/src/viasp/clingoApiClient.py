import json
from typing import Collection

import requests
from .shared.defaults import DEFAULT_BACKEND_URL
from .shared.io import DataclassJSONEncoder
from .shared.model import ClingoMethodCall, StableModel
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
            log(f"Backend at is unavailable ({DEFAULT_BACKEND_URL})", Level.WARN)

    def is_available(self):
        return backend_is_running(self.backend_url)

    def register_function_call(self, name, sig, args, kwargs):
        serializable_call = ClingoMethodCall.merge(name, sig, args, kwargs)
        self._register_function_call(serializable_call)

    def _register_function_call(self, call: ClingoMethodCall):
        if backend_is_running():
            serialized = json.dumps(call, cls=DataclassJSONEncoder)
            r = requests.post(f"{self.backend_url}/control/add_call",
                              data=serialized,
                              headers={'Content-Type': 'application/json'})
            if not r.ok:
                error(f"{r.status_code} {r.reason}")

    def set_target_stable_model(self, stable_models: Collection[StableModel]):
        serialized = json.dumps(stable_models, cls=DataclassJSONEncoder)
        r = requests.post(f"{self.backend_url}/control/models", data=serialized,
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
            error(f"Drawing failed [{r.status_code}] ({r.reason})")

    def _reconstruct(self):
        r = requests.get(f"{self.backend_url}/control/reconstruct")
        if r.ok:
            log(f"Reconstructing in progress.")
        else:
            error(f"Reconstructing failed [{r.status_code}] ({r.reason})")
