from copy import copy
from dataclasses import dataclass, field
from enum import Enum
from inspect import Signature as inspect_Signature
from typing import Any, Sequence, Dict, Union, FrozenSet, Collection
from uuid import UUID, uuid4

from clingo import Symbol, ModelType
from clingo.ast import AST


@dataclass()
class Node:
    diff: FrozenSet[Symbol] = field(hash=True)
    rule_nr: int = field(hash=True)
    atoms: FrozenSet[Symbol] = field(default_factory=frozenset, hash=True)
    uuid: UUID = field(default_factory=uuid4, hash=False)

    def __hash__(self):
        return hash((self.atoms, self.rule_nr, self.diff))

    def __eq__(self, o):
        return isinstance(o, type(self)) and (self.atoms, self.rule_nr, self.diff) == (o.atoms, o.rule_nr, o.diff)

    def __repr__(self):
        return f"Node(diff={{{'. '.join(map(str, self.diff))}}}, rule_nr={self.rule_nr}, atoms={{{'. '.join(map(str, self.atoms))}}}, uuid={self.uuid})"


@dataclass(frozen=True)
class Transformation:
    id: int
    rules: Sequence[str]

    def __hash__(self):
        return hash(tuple(self.rules))


@dataclass(frozen=True)
class Signature:
    name: str
    args: int


@dataclass
class ClingoMethodCall:
    name: str
    kwargs: Dict[str, Any]
    uuid: Union[UUID, None] = field(default_factory=uuid4)

    @classmethod
    def merge(cls, name: str, signature: inspect_Signature, args: Sequence[Any], kwargs: Dict[str, Any]):
        args_dict = copy(kwargs)
        param_names = list(signature.parameters)
        for index, arg in enumerate(args):
            args_dict[param_names[index]] = arg
        return cls(name, args_dict)


@dataclass
class StableModel:
    cost: Collection[int]
    optimality_proven: bool
    type: ModelType
    atoms: Collection[Symbol]
    terms: Collection[Symbol]
    shown: Collection[Symbol]
    theory: Collection[Symbol]


class FailedReason(Enum):
    WARNING = "WARNING"
    FAILURE = "FAILURE"


@dataclass
class TransformationError:
    ast: AST
    reason: FailedReason
