from collections import defaultdict
from typing import Dict, List, Tuple, Iterable, Set, Collection, Any, Union

import clingo
import networkx as nx
from clingo import ast, Symbol
from clingo.ast import Transformer, parse_string, Rule, ASTType, AST, Literal, Minimize, Disjunction

from .utils import is_constraint, merge_constraints, topological_sort
from ..asp.utils import merge_cycles, remove_loops
from viasp.asp.ast_types import SUPPORTED_TYPES, ARITH_TYPES, UNSUPPORTED_TYPES, UNKNOWN_TYPES
from ..shared.model import Transformation, TransformationError, FailedReason
from ..shared.simple_logging import warn, error


def is_fact(rule, dependencies):
    return len(rule.body) == 0 and not len(dependencies)


def make_signature(literal: clingo.ast.Literal) -> Tuple[str, int]:
    if str(literal.atom.ast_type) == "ASTType.BodyAggregate":
        return literal, 0
    unpacked = literal.atom.symbol
    return unpacked.name, len(unpacked.arguments) if hasattr(unpacked, "arguments") else 0


def filter_body_arithmetic(elem: clingo.ast.Literal):
    return elem.atom.ast_type not in ARITH_TYPES


class FilteredTransformer(Transformer):

    def __init__(self, accepted=None, forbidden=None, warning=None):
        if accepted is None:
            accepted = SUPPORTED_TYPES
        if forbidden is None:
            forbidden = UNSUPPORTED_TYPES
        if warning is None:
            warning = UNKNOWN_TYPES
        self._accepted: Collection[ASTType] = accepted
        self._forbidden: Collection[ASTType] = forbidden
        self._warnings: Collection[ASTType] = warning
        self._filtered: List[TransformationError] = []

    def will_work(self):
        return all(f.reason != FailedReason.FAILURE for f in self._filtered)

    def get_filtered(self):
        return self._filtered

    def visit(self, ast: AST, *args: Any, **kwargs: Any) -> Union[AST, None]:
        """
        Dispatch to a visit method in a base class or visit and transform the
        children of the given AST if it is missing.
        """
        if ast.ast_type in self._forbidden:
            error(f"Filtering forbidden part of clingo language {ast} ({ast.ast_type})")
            self._filtered.append(TransformationError(ast, FailedReason.FAILURE))
            return
        if ast.ast_type in self._warnings:
            warn(
                f"Found unsupported part of clingo language {ast} ({ast.ast_type})\nThis may lead to faulty visualizations!")
            self._filtered.append(TransformationError(ast, FailedReason.WARNING))
        attr = 'visit_' + str(ast.ast_type).replace('ASTType.', '')
        if hasattr(self, attr):
            return getattr(self, attr)(ast, *args, **kwargs)
        return ast.update(**self.visit_children(ast, *args, **kwargs))


class DependencyCollector(Transformer):

    def visit_Aggregate(self, aggregate, deps={}, names=set()):
        conditional_literals = aggregate.elements
        for elem in conditional_literals:
            self.visit(elem, deps=deps)
        return aggregate

    def visit_ConditionalLiteral(self, conditional_literal, deps={}, names=set()):
        self.visit(conditional_literal.literal)
        deps[conditional_literal.literal] = []
        for condition in conditional_literal.condition:
            deps[conditional_literal.literal].append(condition)
        return conditional_literal


class NameCollector(Transformer):

    def visit_Variable(self, variable, deps={}, names=set()):
        # self.visit(variable.term, names=names)
        names.add(variable.name)
        return variable


class ProgramAnalyzer(DependencyCollector, FilteredTransformer, NameCollector):
    """
    Receives a ASP program and finds it's dependencies within, can sort a program by it's dependencies.
    """

    def __init__(self):
        super().__init__()
        # TODO: self.dependencies can go?
        self.dependencies = nx.DiGraph()
        self.dependants: Dict[Tuple[str, int], Set[Rule]] = defaultdict(set)
        self.conditions: Dict[Tuple[str, int], Set[Rule]] = defaultdict(set)
        self.positive_conditions: Dict[Tuple[str, int], Set[Rule]] = defaultdict(set)
        self.rule2signatures = defaultdict(set)
        self.facts: Set[Symbol] = set()
        self.constants: Set[Symbol] = set()
        self.constraints: Set[Rule] = set()
        self.pass_through: Set[AST] = set()
        self.rules: List[Rule] = []
        self.names: Set[str] = set()

    def _get_conflict_free_version_of_name(self, name: str) -> Collection[str]:
        candidates = [name for name, _ in self.dependants.keys()]
        candidates.extend([name for name, _ in self.conditions.keys()])
        candidates.extend([fact.atom.symbol.name for fact in self.facts])
        candidates.extend([name for name in self.names])
        candidates = set(candidates)
        current_best = name
        for _ in range(10):
            if current_best in candidates:
                current_best = f"{current_best}_"
            else:
                return current_best
        raise ValueError(f"Could not create conflict free variable name for {name}!")

    def get_conflict_free_h(self):
        return self._get_conflict_free_version_of_name("h")

    def get_conflict_free_model(self):
        return self._get_conflict_free_version_of_name("model")

    def get_conflict_free_variable(self):
        """
        For use in the replacement of Intervals.
        By a new conflict free (unique) variable.
        The new variable is added to the set of known variables.
        """
        new_var = self._get_conflict_free_version_of_name("X")
        self.names = self.names.union({new_var})
        return new_var

    def get_facts(self):
        return extract_symbols(self.facts, self.constants)

    def get_constants(self):
        return self.constants

    def register_symbolic_dependencies(self, deps: Dict[Literal, List[Literal]]):
        for u, conditions in deps.items():
            for v in conditions:
                self.dependencies.add_edge(u, v)

    def register_rule_conditions(self, rule: AST, conditions: List[Literal]) -> None:
        for c in conditions:
            c_sig = make_signature(c)
            self.conditions[c_sig].add(rule)

    def register_rule_dependencies(self, rule: Rule, deps: Dict[Literal, List[Literal]]) -> None:
        for uu in deps.values():
            for u in uu:
                u_sig = make_signature(u)
                self.conditions[u_sig].add(rule)
                for l in rule.body:
                    if l.atom.ast_type == ASTType.SymbolicAtom:
                        if (l.atom.symbol.name == u.atom.symbol.name and \
                            l.sign == ast.Sign.NoSign):
                            self.positive_conditions[u_sig].add(rule)
                    

        for v in filter(lambda symbol: symbol.atom.ast_type != ASTType.BooleanConstant, deps.keys()):
            v_sig = make_signature(v)
            self.dependants[v_sig].add(rule)

    def visit_Rule(self, rule: Rule):
        deps = defaultdict(list)
        names = set()
        _ = self.visit(rule.head, deps=deps, names=names)
        for b in rule.body:
            self.visit(b, deps=deps, names=names)

        if is_fact(rule, deps):
            self.facts.add(rule.head)
        if not len(deps) and len(rule.body):
            deps[rule.head] = []
        for _, cond in deps.items():
            cond.extend(filter(filter_body_arithmetic, rule.body))
        self.register_symbolic_dependencies(deps)
        self.names = self.names.union(names)
        self.register_rule_dependencies(rule, deps)
        self.rules.append(rule)


    def visit_Minimize(self, minimize: Minimize):
        deps = defaultdict(list)
        self.pass_through.add(minimize)

        return minimize

    def visit_Definition(self, definition):
        self.constants.add(definition)
        return definition

    def add_program(self, program: str) -> None:
        parse_string(program, lambda statement: self.visit(statement))

    def sort_program(self, program) -> List[Transformation]:
        parse_string(program, lambda rule: self.visit(rule))
        sorted_program = self.sort_program_by_dependencies()
        return [Transformation(i, prg) for i, prg in enumerate(sorted_program)]

    def get_sorted_program(self) -> List[Transformation]:
        sorted_program = self.sort_program_by_dependencies()
        return [Transformation(i, prg) for i, prg in enumerate(sorted_program)]

    def make_dependency_graph(self, head_dependencies: Dict[Tuple[str, int], Iterable[clingo.ast.AST]],
                              body_dependencies: Dict[Tuple[str, int], Iterable[clingo.ast.AST]]) -> nx.DiGraph:
        """
        We draw a dependency graph based on which rule head contains which literals.
        That way we know, that in order to have a rule r with a body containing literal l, all rules that have l in their
        heads must come before r.
        :param head_dependencies: Mapping from a signature to all rules containing them in the head
        :param body_dependencies: mapping from a signature to all rules containing them in the body
        :return:
        """
        g = nx.DiGraph()

        for deps in head_dependencies.values():
            for dep in deps:
                g.add_node(frozenset([dep]))
        for deps in body_dependencies.values():
            for dep in deps:
                g.add_node(frozenset([dep]))

        for head_signature, rules_with_head in head_dependencies.items():
            dependent_rules = body_dependencies.get(head_signature, [])
            for parent_rule in rules_with_head:
                for dependent_rule in dependent_rules:
                    g.add_edge(frozenset([parent_rule]), frozenset([dependent_rule]))

        return g

    def sort_program_by_dependencies(self):
        deps = self.make_dependency_graph(self.dependants, self.conditions)
        deps = merge_constraints(deps)
        deps, _ = merge_cycles(deps)
        deps, _ = remove_loops(deps)
        program = topological_sort(deps, self.rules)
        return program

    def check_positive_recursion(self):
        deps1 = self.make_dependency_graph(self.dependants, self.positive_conditions)
        deps1 = merge_constraints(deps1)
        deps2, where1 = merge_cycles(deps1)
        _, where2 = remove_loops(deps2)
        return where1.union(where2)



class ProgramReifier(DependencyCollector):

    def __init__(self, rule_nr=1, h="h", model="model", \
                 get_conflict_free_variable=lambda s: s):
        self.rule_nr = rule_nr
        self.h = h
        self.model = model
        self.get_conflict_free_variable = get_conflict_free_variable

    def _nest_rule_head_in_h_with_explanation_tuple(self, loc: ast.Location,
                dependant: ast.Literal, body: List[ast.Literal]):
        """
        In: H :- B.
        Out: h(0, H, pos_atoms(B)),
        where pos_atoms(B) is a tuple of all positive Symbolic Atoms in B.
        """
        loc_fun = ast.Function(loc, str(self.rule_nr), [], False)
        loc_atm = ast.SymbolicAtom(loc_fun)
        loc_lit = ast.Literal(loc, ast.Sign.NoSign, loc_atm)
        reasons = []
        for literal in body:
            if literal.sign == ast.Sign.NoSign and \
                literal.atom.ast_type == ast.ASTType.SymbolicAtom:
                reasons.append(literal.atom)
        reason_fun = ast.Function(loc, '', reasons, 0)
        reason_lit = ast.Literal(loc, ast.Sign.NoSign, reason_fun)

        return [ast.Function(loc, self.h, [loc_lit, dependant, reason_lit], 0)]

    def visit_Rule(self, rule: clingo.ast.Rule):
        """
        Reify a rule into a set of new rules.
        Also replaces any interval in the head with a variable and adds it to the body.
        In: H :- B.
        Out: h(0, H, pos_atoms(B)) :- H, B.
        where pos_atoms(B), reasons for H, is a tuple of all positive Symbolic Atoms in B.


        :param rule: The rule to reify
        :return: A list of new rules"""
        # Embed the head
        deps = defaultdict(list)
        loc = rule.location
        _ = self.visit(rule.head, deps=deps)

        if is_fact(rule, deps) or is_constraint(rule):
            return [rule]
        if not deps:
            # if it's a "simple head"
            deps[rule.head] = []
        new_rules = []
        for dependant, conditions in deps.items():
            if has_an_interval(dependant):
                # replace dependant with variable: e.g. (1..3) -> X
                variables = [ast.Variable(loc, self.get_conflict_free_variable())
                             if arg.ast_type == ast.ASTType.Interval else arg
                             for arg in dependant.atom.symbol.arguments]
                symbol = ast.SymbolicAtom(ast.Function(loc,
                                                       dependant.atom.symbol.name,
                                                       variables,
                                                       False))
                dependant = ast.Literal(loc, ast.Sign.NoSign, symbol)
            new_head_s = self._nest_rule_head_in_h_with_explanation_tuple(rule.location,
                                                                          dependant,
                                                                          rule.body)
            # Add reified head to body
            new_body = [dependant]
            new_body.extend(rule.body)
            new_body.extend(conditions)
            new_rules.extend([Rule(rule.location, new_head, new_body) for new_head in new_head_s])

        return new_rules


def register_rules(rule_or_list_of_rules, rulez):
    if isinstance(rule_or_list_of_rules, list):
        for rule in rule_or_list_of_rules:
            if not rule in rulez:
                rulez.extend(rule_or_list_of_rules)
    else:
        if not rule_or_list_of_rules in rulez:
            rulez.append(rule_or_list_of_rules)


def transform(program: str, visitor=None, **kwargs):
    if visitor is None:
        visitor = ProgramReifier(**kwargs)
    rulez = []
    parse_string(program, lambda rule: register_rules(visitor.visit(rule), rulez))
    return rulez


def reify(transformation: Transformation, **kwargs):
    visitor = ProgramReifier(transformation.id, **kwargs)
    result = []
    for rule in transformation.rules:
        result.extend(visitor.visit(rule))
    return result


def reify_list(transformations: Iterable[Transformation], **kwargs) -> List[AST]:
    reified = []
    for part in transformations:
        reified.extend(reify(part, **kwargs))
    return reified


def extract_symbols(facts, constants=None):
    if constants is None:
        constants = set()
    ctl = clingo.Control()
    ctl.add("INTERNAL", [], "".join(f"{str(f)}." for f in facts))
    ctl.add("INTERNAL", [], "".join(f"{str(c)}" for c in constants))
    ctl.ground([("INTERNAL", [])])
    result = []
    for fact in ctl.symbolic_atoms:
        result.append(fact.symbol)
    return result

def has_an_interval(literal):
    """
    Checks if a literal has an interval as one of its symbols.
    Returns false if an attribute error occurs.
    """
    try:
        for arg in literal.atom.symbol.arguments:
            if arg.ast_type == ast.ASTType.Interval:
                return True
    except AttributeError:
        return False
    return False
