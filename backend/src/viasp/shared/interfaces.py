from abc import ABC, abstractmethod
from typing import Sequence, Any, Dict, Collection
from inspect import Signature as inspect_Signature

from viasp.shared.model import StableModel


class ViaspClient(ABC):

    @abstractmethod
    def is_available(self):
        pass

    @abstractmethod
    def register_function_call(self, name: str, sig: inspect_Signature,
                               args: Sequence[Any], kwargs: Dict[str, Any]):
        pass

    @abstractmethod
    def set_target_stable_model(self, stable_models: Collection[StableModel]):
        pass

    @abstractmethod
    def show(self):
        pass
