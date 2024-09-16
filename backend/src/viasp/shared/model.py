from copy import copy
from dataclasses import dataclass, field
from enum import Enum
from inspect import Signature as inspect_Signature
from re import U
from typing import Any, Sequence, Dict, Union, FrozenSet, Collection, List, Tuple
from types import MappingProxyType
from uuid import UUID, uuid4
import networkx as nx

from clingo import Symbol, ModelType
from clingo.ast import AST, Transformer
from .util import DefaultMappingProxyType, hash_transformation_rules, get_rules_from_input_program, get_ast_from_input_string

@dataclass()
class SymbolIdentifier:
    symbol: Symbol = field(hash=True)
    has_reason: bool = field(default=False, hash=False)
    uuid: UUID = field(default_factory=uuid4, hash=False)

    def __eq__(self, other):
        if isinstance(other, SymbolIdentifier):
            return self.symbol == other.symbol
        elif isinstance(other, Symbol):
            return self.symbol == other

    def __hash__(self):
        return hash(self.symbol)

    def __repr__(self):
        return f"{{symbol: {str(self.symbol)}, uuid: {self.uuid}}}"


@dataclass()
class Node:
    diff: FrozenSet[SymbolIdentifier] = field(hash=True)
    rule_nr: int = field(hash=True)
    atoms: FrozenSet[SymbolIdentifier] = field(default_factory=frozenset, hash=True)
    reason: Union[
        Dict[str, List[Symbol]],
        MappingProxyType] \
        = field(default_factory=DefaultMappingProxyType, hash=True)
    recursive: List = field(default_factory=list, hash=False)
    space_multiplier: float = field(default=1.0, hash=False)
    uuid: UUID = field(default_factory=uuid4, hash=False)

    def __hash__(self):
        return hash((self.atoms, self.rule_nr, self.diff))

    def __eq__(self, o):
        return isinstance(o, type(self)) and (
            self.atoms, self.rule_nr, self.diff, self.reason,
            self.space_multiplier) == (o.atoms, o.rule_nr, o.diff, o.reason,
                                       o.space_multiplier)

    def __repr__(self):
        repr_reasons = []
        if isinstance(self.reason, list):
            repr_reasons = [str(reason) for reason in self.reason]
        else:
            for key, val in self.reason.items():
                repr_reasons.append(f"{key}: [{', '.join(map(str,val))}]")
        return f"Node(diff={{{'. '.join(map(str, self.diff))}}}, rule_nr={self.rule_nr}, atoms={{{', '.join(map(str,self.atoms))}}}, reasons={{{', '.join(repr_reasons)}}}, recursive={self.recursive}, space_multiplier={self.space_multiplier}, uuid={self.uuid})"


@dataclass()
class ClingraphNode:
    uuid: UUID = field(default_factory=uuid4, hash=True)

    def __hash__(self):
        return hash(self.uuid)

    def __eq__(self, o):
        return isinstance(o, type(self)) and self.uuid == o.uuid

    def __repr__(self):
        return f"ClingraphNode(uuid={self.uuid})"

@dataclass(frozen=False)
class RuleContainer:
    ast: Tuple[AST, ...] = field(default_factory=tuple, hash=True)
    str_: Tuple[str, ...] = field(default_factory=tuple, hash=False)

    def __post_init__(self):
        if isinstance(self.ast, AST):
            self.ast = (self.ast, )
        if isinstance(self.ast, List):
            self.ast = tuple(self.ast)
        if isinstance(self.str_, str):
            self.str_ = (self.str_, )
        if isinstance(self.str_, List):
            self.str_ = tuple(self.str_)

        if len(self.str_) == 0 and len(self.ast) > 0:
            self.str_ = tuple(get_rules_from_input_program(self.ast))
        if len(self.ast) == 0 and len(self.str_) > 0:
            self.ast = tuple(get_ast_from_input_string(self.str_))
    
    def __hash__(self):
        return hash(self.ast)

    def __eq__(self, o):
        return isinstance(o, type(self)) and self.ast == o.ast

    def __repr__(self):
        return str(self.str_)


@dataclass(frozen=False)
class Transformation:
    id: int = field(hash=True)
    rules: RuleContainer = field(default_factory=RuleContainer, hash=True)
    adjacent_sort_indices: Dict[str, int] = field(default_factory=dict, hash=False)
    hash: str = field(default="", hash=True)

    def __post_init__(self):
        if isinstance(self.rules, AST):
            self.rules = RuleContainer(ast=(self.rules,))
        if isinstance(self.rules, List):
            self.rules = RuleContainer(ast=tuple(self.rules))
        if isinstance(self.rules, Tuple):
            self.rules = RuleContainer(ast=self.rules)
        if self.hash == "":
            self.hash = hash_transformation_rules(self.rules.ast)

    def __hash__(self):
        return hash(self.rules.ast)

    def __eq__(self, o):
        if not isinstance(o, type(self)):
            return False
        if self.id != o.id:
            return False
        if len(self.rules.ast) != len(o.rules.ast):
            return False
        for r in o.rules.ast:
            if r not in self.rules.ast:
                return False
        return True

    def __repr__(self):
        return f"Transformation(id={self.id}, rules={self.rules}, adjacent_sort_indices={self.adjacent_sort_indices}, hash={self.hash})"




@dataclass(frozen=True)
class Signature:
    name: str
    args: int


@dataclass
class ClingoMethodCall:
    name: str
    kwargs: Dict[str, Any]
    uuid: UUID = field(default_factory=uuid4)

    @classmethod
    def merge(cls, name: str, signature: inspect_Signature, args: Sequence[Any], kwargs: Dict[str, Any]):
        args_dict = copy(kwargs)
        param_names = list(signature.parameters)
        for index, arg in enumerate(args):
            args_dict[param_names[index]] = arg
        return cls(name, args_dict)


@dataclass
class StableModel:
    cost: Collection[int] = field(default_factory=list)
    optimality_proven: bool = field(default=False)
    type: ModelType = field(default=ModelType.StableModel)
    atoms: Collection[Symbol] = field(default_factory=list)
    terms: Collection[Symbol] = field(default_factory=list)
    shown: Collection[Symbol] = field(default_factory=list)
    theory: Collection[Symbol] = field(default_factory=list)

    def __eq__(self, o):
        return isinstance(o, type(self)) and set(self.atoms) == set(o.atoms)

    def __hash__(self):
        return hash(tuple(self.atoms))

    def symbols(self,
                atoms: bool = False,
                terms: bool = False,
                shown: bool = False,
                theory: bool = False) -> Sequence[Symbol]:
        symbols = []
        if atoms:
            symbols.extend(self.atoms)
        if terms:
            symbols.extend(self.terms)
        if shown:
            symbols.extend(self.shown)
        if theory:
            symbols.extend(self.theory)
        return symbols


class FailedReason(Enum):
    WARNING = "WARNING"
    FAILURE = "FAILURE"


@dataclass
class TransformationError:
    ast: AST
    reason: FailedReason

@dataclass
class TransformerTransport:
    transformer: Transformer
    imports: str
    path: str

    @classmethod
    def merge(cls, transformer: Transformer, imports: str, path: str):
        return cls(transformer, imports, path)
