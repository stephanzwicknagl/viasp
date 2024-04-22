import json

from json import JSONDecoder, JSONEncoder
# Legacy: To be deleted in Version 3.0
# from enum import IntEnum
from flask.json.provider import JSONProvider
from dataclasses import is_dataclass
from typing import Union, Collection, Iterable, Sequence, cast, Tuple
from pathlib import PosixPath
from uuid import UUID
import os
import sys
import importlib.util


import inspect
import base64
import types

import clingo
import networkx as nx
# Legacy: To be deleted in Version 3.0
# from _clingo.lib import clingo_model_type_brave_consequences, clingo_model_type_cautious_consequences, \
#     clingo_model_type_stable_model
from clingo import Model as clingo_Model, ModelType, Symbol, Application
from clingo.ast import AST, ASTType

from .interfaces import ViaspClient
from .model import Node, ClingraphNode, Transformation, Signature, StableModel, ClingoMethodCall, TransformationError, FailedReason, SymbolIdentifier, TransformerTransport, RuleContainer

class DataclassJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, cls=DataclassJSONEncoder, **kwargs)

    def loads(self, s, **kwargs):
        return json.loads(s, cls=DataclassJSONDecoder, **kwargs)

def model_to_json(model: Union[clingo_Model, Collection[clingo_Model]], *args, **kwargs) -> str:
    return json.dumps(model, *args, cls=DataclassJSONEncoder, **kwargs)


def object_hook(obj):
    if '_type' not in obj:
        return obj
    t = obj['_type']
    del obj['_type']
    if t == "Function":
        return clingo.Function(**obj)
    elif t == "Number":
        return clingo.Number(**obj)
    elif t == "String":
        return clingo.String(**obj)
    elif t == "Infimum":
        return clingo.Infimum
    elif t == "Supremum":
        return clingo.Supremum
    elif t == "Node":
        obj['atoms'] = frozenset(obj['atoms'])
        obj['diff'] = frozenset(obj['diff'])
        return Node(**obj)
    elif t == "ClingraphNode":
        return ClingraphNode(**obj)
    elif t == "Transformation":
        return Transformation(**obj)
    elif t == "RuleContainer":
        return RuleContainer(str_=obj["str_"])
    elif t == "Signature":
        return Signature(**obj)
    elif t == "Graph":
        return nx.node_link_graph(obj["_graph"])
    elif t == "StableModel":
        return StableModel(**obj)
    elif t == "ModelType":
        return ModelType.StableModel
    elif t == "ClingoMethodCall":
        return ClingoMethodCall(**obj)
    elif t == "SymbolIdentifier":
        return SymbolIdentifier(**obj)
    elif t == "Transformer":
        return reconstruct_transformer(obj)
    return obj


class DataclassJSONDecoder(JSONDecoder):
    def __init__(self, *args, **kwargs):
        JSONDecoder.__init__(self, object_hook=object_hook, *args, **kwargs)


def dataclass_to_dict(o):
    if isinstance(o, Node):
        sorted_atoms = sorted(o.atoms, key=lambda x: x.symbol)
        sorted_diff = sorted(o.diff, key=lambda x: x.symbol)
        sorted_reason = {} if len(o.reason) == 0 else o.reason
        return {"_type": "Node",
                "atoms": sorted_atoms,
                "diff": sorted_diff,
                "reason": sorted_reason,
                "recursive": o.recursive,
                "uuid": o.uuid,
                "rule_nr": o.rule_nr,
                "space_multiplier": o.space_multiplier}
    elif isinstance(o, ClingraphNode):
        return {"_type": "ClingraphNode", "uuid": o.uuid}
    elif isinstance(o, TransformationError):
        return {"_type": "TransformationError", "ast": o.ast, "reason": o.reason}
    elif isinstance(o, SymbolIdentifier):
        return {"_type": "SymbolIdentifier", "symbol": o.symbol, "has_reason": o.has_reason, "uuid": o.uuid}
    elif isinstance(o, Signature):
        return {"_type": "Signature", "name": o.name, "args": o.args}
    elif isinstance(o, Transformation):
        return {
            "_type": "Transformation",
            "id": o.id,
            "rules": o.rules,
            "adjacent_sort_indices": o.adjacent_sort_indices,
            "hash": o.hash
        }
    elif isinstance(o, RuleContainer):
        return {"_type": "RuleContainer", "ast": o.ast, "str_": o.str_}
    elif isinstance(o, StableModel):
        return {"_type": "StableModel", "cost": o.cost, "optimality_proven": o.optimality_proven, "type": o.type,
                "atoms": o.atoms, "terms": o.terms, "shown": o.shown, "theory": o.theory}
    elif isinstance(o, ClingoMethodCall):
        return {"_type": "ClingoMethodCall", "name": o.name, "kwargs": o.kwargs, "uuid": o.uuid}
    elif isinstance(o, TransformerTransport):
        # Get the class definition as a string
        class_definition = inspect.getsource(o.transformer)
        transformer_bytes = base64.b64encode(
            class_definition.encode('utf-8')).decode('utf-8')

        o_json = {"_type": "Transformer",
                  "Transformer_definition": transformer_bytes,
                  "Imports": o.imports,
                  "Path": o.path}
        return o_json
    else:
        raise Exception(f"I/O for {type(o)} not implemented!")


class DataclassJSONEncoder(JSONEncoder):
    def default(self, o):
        encoded = encode_object(o)
        if encoded is not None:
            return encoded
        return super().default(o)


def encode_object(o):
    if isinstance(o, clingo_Model):
        x = model_to_dict(o)
        return x
    elif isinstance(o, ViaspClient):
        return {"_type": "ViaspClient"}
    elif isinstance(o, Application):
        return {"_type": "Application"}
    elif isinstance(o, PosixPath):
        return str(o)
    elif isinstance(o, ModelType):
        return {"_type": "ModelType", "__enum__": str(o)}
    elif isinstance(o, Symbol):
        x = symbol_to_dict(o)
        return x
    elif isinstance(o, FailedReason):
        return {"_type": "FailedReason", "value": o.value}
    elif is_dataclass(o):
        result = dataclass_to_dict(o)
        return result
    elif isinstance(o, nx.Graph):
        return {"_type": "Graph", "_graph": nx.node_link_data(o)}
    elif isinstance(o, UUID):
        return o.hex
    elif isinstance(o, frozenset):
        return list(o)
    elif isinstance(o, set):
        return list(o)
    elif isinstance(o, AST):
        return str(o)
    elif isinstance(o, Iterable):
        return list(o)



def model_to_dict(model: clingo_Model) -> dict:
    model_dict = {"cost": model.cost, "optimality_proven": model.optimality_proven, "type": model.type,
                  "atoms": model.symbols(atoms=True), "terms": model.symbols(terms=True),
                  "shown": model.symbols(shown=True),
                  "theory": model.symbols(theory=True), "_type": "StableModel"}
    return model_dict


def clingo_model_to_stable_model(model: clingo_Model) -> StableModel:
    return StableModel(
        model.cost,
        model.optimality_proven,
        model.type,
        cast(Collection[Symbol], encode_object(model.symbols(atoms=True))),
        cast(Collection[Symbol], encode_object(model.symbols(terms=True))),
        cast(Collection[Symbol], encode_object(model.symbols(shown=True))),
        cast(Collection[Symbol], encode_object(model.symbols(theory=True))),
        )

def clingo_symbols_to_stable_model(atoms: Iterable[Symbol]) -> StableModel:
    return StableModel(atoms=cast(Collection[Symbol], encode_object(atoms)))

def symbol_to_dict(symbol: clingo.Symbol) -> dict:
    symbol_dict = {}
    if symbol.type == clingo.SymbolType.Function:
        symbol_dict["_type"] = "Function"
        symbol_dict["name"] = symbol.name
        symbol_dict["positive"] = symbol.positive
        symbol_dict["arguments"] = symbol.arguments
    elif symbol.type == clingo.SymbolType.Number:
        symbol_dict["number"] = symbol.number
        symbol_dict["_type"] = "Number"
    elif symbol.type == clingo.SymbolType.String:
        symbol_dict["string"] = symbol.string
        symbol_dict["_type"] = "String"
    elif symbol.type == clingo.SymbolType.Infimum:
        symbol_dict["_type"] = "Infimum"
    elif symbol.type == clingo.SymbolType.Supremum:
        symbol_dict["_type"] = "Supremum"
    return symbol_dict


# Legacy: To be deleted in Version 3.0
# class viasp_ModelType(IntEnum):
#     """
#     Enumeration of the different types of models.
#     """
#     BraveConsequences = clingo_model_type_brave_consequences
#     """
#     The model stores the set of brave consequences.
#     """
#     CautiousConsequences = clingo_model_type_cautious_consequences
#     """
#     The model stores the set of cautious consequences.
#     """
#     StableModel = clingo_model_type_stable_model
#     """
#     The model captures a stable model.
#     """

#     @classmethod
#     def from_clingo_ModelType(cls, clingo_ModelType: ModelType):
#         if clingo_ModelType.name == cls.BraveConsequences.name:
#             return cls.BraveConsequences
#         elif clingo_ModelType.name == cls.StableModel.name:
#             return cls.StableModel
#         else:
#             return cls.CautiousConsequences


# class ClingoModelEncoder(JSONEncoder):
#     def default(self, o: Any) -> Any:
#         if isinstance(o, clingo_Model):
#             x = model_to_dict(o)
#             return x
#         elif isinstance(o, ModelType):
#             if o in [ModelType.CautiousConsequences, ModelType.BraveConsequences, ModelType.StableModel]:
#                 return {"__enum__": str(o)}
#             return super().default(o)
#         elif isinstance(o, Symbol):
#             x = symbol_to_dict(o)
#             return x
#         return super().default(o)


def reconstruct_transformer(obj: dict) -> TransformerTransport:
    # Reconstruct the class definition
    # Get the path to the module containing MyClass
    my_module_path = obj["Path"]
    # Add the directory containing my_module to sys.path
    my_module_dir = os.path.dirname(my_module_path)
    sys.path.append(my_module_dir)
    # Load the module containing MyClass
    module_name = os.path.splitext(os.path.basename(my_module_path))[0]
    module_spec = importlib.util.spec_from_file_location(
        module_name, my_module_path)
    if module_spec is None or module_spec.loader is None:
        raise Exception(f"Module {module_name} not found!")
    my_module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(my_module)

    # Create a temporary module to hold the class definition
    module_name = '__temp_module__'
    module = types.ModuleType(module_name)

    # get the string
    class_definition_str = obj["Imports"] + "\n" \
                        + base64.b64decode(obj["Transformer_definition"])\
                                .decode('utf-8')

    # Add the module's original package to sys.path
    module.__file__ = my_module.__file__
    sys.modules[module_name] = module

    # Execute the class definition in the temporary module
    exec(class_definition_str, module.__dict__)
    return getattr(module, "Transformer")
