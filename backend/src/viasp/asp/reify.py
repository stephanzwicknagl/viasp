from collections import defaultdict
from typing import Dict, List, Tuple, Iterable, Set, Collection, Any, Union, Sequence, Generator, Optional, cast

import clingo
import networkx as nx
from clingo import ast, Symbol
from clingo.ast import (
    Transformer,
    parse_string,
    ASTType,
    AST,
)

from .utils import is_constraint, merge_constraints, rank_topological_sorts
from ..asp.utils import merge_cycles, remove_loops
from viasp.asp.ast_types import (
    SUPPORTED_TYPES,
    ARITH_TYPES,
    UNSUPPORTED_TYPES,
    UNKNOWN_TYPES,
)
from ..shared.model import Transformation, TransformationError, FailedReason
from ..shared.simple_logging import warn, error


def is_fact(rule, dependencies):
    return len(rule.body) == 0 and not len(dependencies)


def make_signature(literal: ast.Literal) -> Tuple[str, int]: # type: ignore
    if literal.atom.ast_type in [ASTType.BodyAggregate]:
        return literal, 0
    unpacked = literal.atom.symbol
    if hasattr(unpacked, "ast_type") and unpacked.ast_type == ASTType.Pool:
        unpacked = unpacked.arguments[0]
    return (
        unpacked.name,
        len(unpacked.arguments) if hasattr(unpacked, "arguments") else 0,
    )


def filter_body_arithmetic(elem: ast.Literal): # type: ignore
    elem_ast_type = getattr(getattr(elem, "atom", ""), "ast_type", None)
    return elem_ast_type not in ARITH_TYPES


def separate_body_conditionals(body: Sequence[AST]) -> List[AST]:
    separated: List[AST] = []
    for body_elem in body:
        if body_elem.ast_type == ASTType.ConditionalLiteral:
            separated.append(cast(AST, body_elem.literal))
            separated.extend(cast(Iterable[AST], body_elem.condition))
        else:
            separated.append(body_elem)
    return separated


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
            error(
                f"Filtering forbidden part of clingo language {ast} ({ast.ast_type})"
            )
            self._filtered.append(
                TransformationError(ast, FailedReason.FAILURE))
            return
        if ast.ast_type in self._warnings:
            warn(
                f"Found unsupported part of clingo language {ast} ({ast.ast_type})\nThis may lead to faulty visualizations!"
            )
            self._filtered.append(
                TransformationError(ast, FailedReason.WARNING))
        attr = "visit_" + str(ast.ast_type).replace("ASTType.", "")
        if hasattr(self, attr):
            return getattr(self, attr)(ast, *args, **kwargs)
        return ast.update(**self.visit_children(ast, *args, **kwargs))


class DependencyCollector(Transformer):

    def visit_Aggregate(self, aggregate: ast.Aggregate, **kwargs: Any) -> AST: # type: ignore
        kwargs.update({"in_aggregate": True})
        new_body = kwargs.get("new_body", [])

        aggregate_update = aggregate.update(
            **self.visit_children(aggregate, **kwargs))
        new_body.append(aggregate_update)
        return aggregate_update

    def visit_BodyAggregateElement(self, aggregate: ast.BodyAggregateElement, **kwargs: Any) -> AST: # type: ignore
        # update flag
        kwargs.update({"in_aggregate": True})

        # collect conditions
        conditions = kwargs.get("body_aggregate_elements", [])
        conditions.extend(aggregate.condition)
        return aggregate.update(**self.visit_children(aggregate, **kwargs))

    def visit_ConditionalLiteral(self, conditional_literal: ast.ConditionalLiteral, # type: ignore
                                 **kwargs: Any) -> AST:
        deps = kwargs.get("deps", {})
        new_body = kwargs.get("new_body", [])
        in_head = kwargs.get("in_head", False)
        body_aggregate_elements = kwargs.get("body_aggregate_elements", [])

        if in_head:
            deps[conditional_literal.literal] = []
            for condition in conditional_literal.condition:
                deps[conditional_literal.literal].append(condition)
            new_body.extend(conditional_literal.condition)
        else:
            body_aggregate_elements.append(conditional_literal.literal)
            for condition in filter(filter_body_arithmetic,
                                    conditional_literal.condition):
                body_aggregate_elements.append(condition)
        return conditional_literal.update(
            **self.visit_children(conditional_literal, **kwargs))

    def visit_Literal(self, literal: ast.Literal, **kwargs: Any) -> AST: # type: ignore
        reasons: List[AST] = kwargs.get("reasons", [])
        new_body: List[AST] = kwargs.get("new_body", [])

        literal_update = literal.update(
            **self.visit_children(literal, **kwargs))

        atom: AST = literal.atom
        if (literal.sign == ast.Sign.NoSign
                and atom.ast_type == ASTType.SymbolicAtom):
            reasons.append(atom)
        new_body.append(literal_update)
        return literal.update(**self.visit_children(literal, **kwargs))

    def visit_Variable(self, variable: ast.Variable, **kwargs: Any) -> AST: # type: ignore
        # rename if necessary
        rename_variables: bool = kwargs.get("rename_variables", False)
        in_aggregate: bool = kwargs.get("in_aggregate", False)
        if rename_variables and in_aggregate:
            return ast.Variable(variable.location, f"_{variable.name}")
        return variable.update(**self.visit_children(variable, **kwargs))

    def visit_BooleanConstant(self, boolean_constant: ast.BooleanConstant, # type: ignore
                              **kwargs: Any) -> AST:
        new_body: List[AST] = kwargs.get("new_body", [])
        new_body.append(boolean_constant)
        return boolean_constant.update(
            **self.visit_children(boolean_constant, **kwargs))


class ProgramAnalyzer(DependencyCollector, FilteredTransformer):
    """
    Receives a ASP program and finds it's dependencies within, can sort a program by it's dependencies.
    """

    def __init__(self):
        super().__init__()
        # TODO: self.dependencies can go?
        self.dependencies = nx.DiGraph()
        self.dependants: Dict[Tuple[str, int], Set[AST]] = defaultdict(set)
        self.conditions: Dict[Tuple[str, int], Set[AST]] = defaultdict(set)
        self.positive_conditions: Dict[Tuple[
            str, int], Set[ast.Rule]] = defaultdict(  # type: ignore
                set)
        self.rule2signatures = defaultdict(set)
        self.facts: Set[Symbol] = set()
        self.constants: Set[Symbol] = set()
        self.constraints: Set[Rule] = set()  # type: ignore
        self.pass_through: Set[AST] = set()
        self.rules: List[ast.Rule] = []  # type: ignore
        self.names: Set[str] = set()
        self.temp_names: Set[str] = set()

    def _get_conflict_free_version_of_name(self, name: str) -> str:
        anti_candidates = self.names.union(self.temp_names)
        current_best = name
        for _ in range(10):
            if current_best in anti_candidates:
                current_best = f"{current_best}_"
            else:
                return current_best
        raise ValueError(
            f"Could not create conflict free variable name for {name}!")

    def get_conflict_free_h(self):
        return self._get_conflict_free_version_of_name("h")

    def get_conflict_free_model(self):
        return self._get_conflict_free_version_of_name("model")

    def get_conflict_free_showTerm(self):
        return self._get_conflict_free_version_of_name("showTerm")

    def get_conflict_free_h_showTerm(self):
        return self._get_conflict_free_version_of_name("h_showTerm")

    def get_conflict_free_variable(self):
        """
        For use in the replacement of Intervals.
        By a new conflict free (unique) variable.
        The new variable is added to the set of known variables.
        """
        try:
            new_var = self._get_conflict_free_version_of_name("X")
        except ValueError:
            new_var = self._get_conflict_free_version_of_name("Y")
        self.temp_names.add(new_var)
        return new_var

    def get_conflict_free_iterindex(self):
        """
        For use in generation of subgraphs at recursive
        transformations.
        """
        return self._get_conflict_free_version_of_name("n")

    def clear_temp_names(self):
        self.temp_names = set()

    def visit_Variable(
            self,
            variable: ast.Variable,  # type: ignore
            **kwargs: Any) -> AST:
        self.names.add(variable.name)
        return variable.update(**self.visit_children(variable, **kwargs))

    def visit_Function(
            self,
            function: ast.Function,  # type: ignore
            **kwargs: Any) -> AST:
        self.names.add(function.name)
        return function.update(**self.visit_children(function, **kwargs))

    def visit_TheoryFunction(
            self,
            theory_function: ast.TheoryFunction,  # type: ignore
            **kwargs: Any) -> AST:
        self.names.add(theory_function.name)
        return theory_function.update(
            **self.visit_children(theory_function, **kwargs))

    def visit_TheoryUnparsedTermElement(
            self,
            theory_unparsed_term_element: ast.
        TheoryUnparsedTermElement,  # type: ignore
            **kwargs: Any) -> AST:
        self.names.update(set(theory_unparsed_term_element.operators))
        return theory_unparsed_term_element.update(
            **self.visit_children(theory_unparsed_term_element, **kwargs))

    def visit_TheoryGuard(
            self,
            theory_guard: ast.TheoryGuard,  # type: ignore
            **kwargs: Any) -> AST:
        self.names.add(theory_guard.operator_name)
        return theory_guard.update(
            **self.visit_children(theory_guard, **kwargs))

    def visit_Definition(
            self,
            definition: ast.Definition,  # type: ignore
            **kwargs: Any) -> AST:
        self.constants.add(definition)

        self.names.add(definition.name)
        return definition.update(**self.visit_children(definition, **kwargs))

    def visit_ShowSignature(
            self,
            show_signature: ast.ShowSignature,  # type: ignore
            **kwargs: Any) -> AST:
        self.names.add(show_signature.name)
        return show_signature.update(
            **self.visit_children(show_signature, **kwargs))

    def visit_Script(
            self,
            script: ast.Script,  # type: ignore
            **kwargs: Any) -> AST:
        self.names.add(script.name)
        return script.update(**self.visit_children(script, **kwargs))

    def visit_Program(
            self,
            program: ast.Program,  # type: ignore
            **kwargs: Any) -> AST:
        self.names.add(program.name)
        return program.update(**self.visit_children(program, **kwargs))

    def visit_Id(self, id: ast.Id, **kwargs: Any) -> AST:  # type: ignore
        self.names.add(id.name)
        return id.update(**self.visit_children(id, **kwargs))

    def visit_ProjectSignature(
            self,
            project_signature: ast.ProjectSignature,  # type: ignore
            **kwargs: Any) -> AST:
        self.names.add(project_signature.name)
        return project_signature.update(
            **self.visit_children(project_signature, **kwargs))

    def visit_TheoryDefinition(
            self,
            theory_definition: ast.TheoryDefinition,  # type: ignore
            **kwargs: Any) -> AST:
        self.names.add(theory_definition.name)
        return theory_definition.update(
            **self.visit_children(theory_definition, **kwargs))

    def visit_TheoryTermDefinition(
            self,
            theory_term_definition: ast.TheoryTermDefinition,  # type: ignore
            **kwargs: Any) -> AST:
        self.names.add(theory_term_definition.name)
        return theory_term_definition.update(
            **self.visit_children(theory_term_definition, **kwargs))

    def visit_TheoryOperatorDefinition(
            self,
            theory_operator_definition: ast.
        TheoryOperatorDefinition,  # type: ignore
            **kwargs: Any) -> AST:
        self.names.add(theory_operator_definition.name)
        return theory_operator_definition.update(
            **self.visit_children(theory_operator_definition, **kwargs))

    def visit_TheoryAtomDefinition(
            self,
            theory_atom_definition: ast.TheoryAtomDefinition,  # type: ignore
            **kwargs: Any) -> AST:
        self.names.add(theory_atom_definition.name)
        return theory_atom_definition.update(
            **self.visit_children(theory_atom_definition, **kwargs))

    def visit_TheoryGuardDefinition(
            self,
            theory_guard_definition: ast.TheoryGuardDefinition,  # type: ignore
            **kwargs: Any) -> AST:
        self.names.update(set(theory_guard_definition.operators))
        self.names.add(theory_guard_definition.term)
        return theory_guard_definition.update(
            **self.visit_children(theory_guard_definition, **kwargs))

    def get_facts(self):
        return extract_symbols(self.facts, self.constants)

    def get_constants(self):
        return list(self.constants)

    def register_symbolic_dependencies(
            self, deps: Dict[ast.Literal, List[ast.Literal]]):  # type: ignore
        for u, conditions in deps.items():
            for v in conditions:
                self.dependencies.add_edge(u, v)

    def register_rule_conditions(
            self,
            rule: ast.Rule,  # type: ignore
            conditions: List[ast.Literal]) -> None:  # type: ignore
        for c in conditions:
            c_sig = make_signature(c)
            self.conditions[c_sig].add(rule)

    def register_rule_dependencies(
            self, rule: ast.Rule, # type: ignore
            deps: Dict[ast.Literal, # type: ignore
                       List[ast.Literal]]) -> None:  # type: ignore
        for uu in deps.values():
            for u in filter(filter_body_arithmetic, uu):
                u_sig = make_signature(u)
                self.conditions[u_sig].add(rule)
                for body_item in rule.body:
                    if (hasattr(body_item, "atom")
                            and hasattr(body_item.atom, "ast_type") and
                            body_item.atom.ast_type == ASTType.SymbolicAtom):
                        if (hasattr(body_item.atom.symbol, "name")
                                and hasattr(u, "atom")
                                and hasattr(u.atom, "symbol")
                                and hasattr(u.atom.symbol, "name")
                                and body_item.atom.symbol.name
                                == u.atom.symbol.name
                                and body_item.sign == ast.Sign.NoSign):
                            self.positive_conditions[u_sig].add(rule)

        for v in filter(
                lambda symbol: symbol.atom.ast_type != ASTType.BooleanConstant
                if (hasattr(symbol, "atom") and hasattr(
                    symbol.atom, "ast_type")) else False,
                deps.keys(),
        ):
            v_sig = make_signature(v)
            self.dependants[v_sig].add(rule)

    def visit_Rule(self, rule: ast.Rule):  # type: ignore
        deps = defaultdict(list)
        _ = self.visit(rule.head, deps=deps, in_head=True)
        for b in rule.body:
            self.visit(b, deps=deps)

        if is_fact(rule, deps):
            self.facts.add(rule.head)
        if not len(deps) and len(rule.body):
            deps[rule.head] = []
        for _, cond in deps.items():
            flattened_body = separate_body_conditionals(rule.body)
            cond.extend(filter(filter_body_arithmetic, flattened_body))
        self.register_symbolic_dependencies(deps)
        self.register_rule_dependencies(rule, deps)
        self.rules.append(rule)

    def get_body_aggregate_elements(self, body: Sequence[AST]) -> List[AST]:
        body_aggregate_elements: List[AST] = []
        for elem in body:
            self.visit(elem, body_aggregate_elements=body_aggregate_elements)
        return body_aggregate_elements

    def get_first_attribute_with_name_from_tree(self, ast: AST,
                                                attribute: str) -> Any:
        while not hasattr(ast, attribute):
            if hasattr(ast, "symbol"):
                ast = cast(AST, ast.symbol)
            else:
                break
        return getattr(ast, attribute, None)

    def visit_ShowTerm(self, showTerm: ast.ShowTerm):  # type: ignore
        deps = defaultdict(list)
        _ = self.visit(showTerm.term, deps=deps, in_head=True)
        for b in showTerm.body:
            self.visit(b, deps=deps)

        if not len(deps) and len(showTerm.body):
            deps[showTerm.term] = []
        for _, cond in deps.items():
            flattened_body = separate_body_conditionals(showTerm.body)
            cond.extend(filter(filter_body_arithmetic, flattened_body))
        self.register_symbolic_dependencies(deps)
        self.register_rule_dependencies(showTerm, deps)
        self.rules.append(showTerm)

    def visit_Minimize(self, minimize: ast.Minimize):  # type: ignore
        deps = defaultdict(list)
        self.pass_through.add(minimize)

        return minimize

    def visit_Defined(self, defined: AST):
        self.pass_through.add(defined)

    def add_program(
            self,
            program: str,
            RegisteredTransformer: Optional[Transformer] = None) -> None:
        if RegisteredTransformer is not None:
            registered_visitor = RegisteredTransformer()  # type: ignore
            new_program: List[AST] = []

            def add(statement):
                nonlocal new_program
                if isinstance(statement, List):
                    new_program.extend(statement)
                else:
                    new_program.append(statement)

            parse_string(
                program,
                lambda statement: add(registered_visitor.visit(statement)))
            for statement in new_program:
                self.visit(statement)
        else:
            parse_string(program,
                         lambda statement: self.visit(statement) and None)

    def sort_program(self, program) -> List[Transformation]:
        parse_string(program, lambda rule: self.visit(rule) and None)
        sorted_programs = self.sort_program_by_dependencies()
        return [
            Transformation(i, prg) for i, prg in enumerate(sorted_programs[0])
        ]

    def get_sorted_program(
            self) -> Generator[List[Transformation], None, None]:
        sorted_programs = self.sort_program_by_dependencies()
        for program in sorted_programs:
            yield [Transformation(i, (prg)) for i, prg in enumerate(program)]

    def make_dependency_graph(
        self,
        head_dependencies: Dict[Tuple[str, int], Set[AST]],
        body_dependencies: Dict[Tuple[str, int], Set[AST]],
    ) -> nx.DiGraph:
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
                    g.add_edge(frozenset([parent_rule]),
                               frozenset([dependent_rule]))

        return g

    def sort_program_by_dependencies(self):
        deps = self.make_dependency_graph(self.dependants, self.conditions)
        deps = merge_constraints(deps)
        deps, _ = merge_cycles(deps)
        deps, _ = remove_loops(deps)
        programs = rank_topological_sorts(nx.all_topological_sorts(deps),
                                          self.rules)
        return programs

    def check_positive_recursion(self):
        deps1 = self.make_dependency_graph(self.dependants,
                                           self.positive_conditions)
        deps1 = merge_constraints(deps1)
        deps2, where1 = merge_cycles(deps1)
        _, where2 = remove_loops(deps2)
        return {
            recursive_set
            for recursive_set in where1.union(where2)
            if self.should_include_recursive_set(recursive_set)
        }

    def should_include_recursive_set(self, recursive_set):
        """
        Drop the set of integrity constraints from the recursive set.
        """
        for rule in recursive_set:
            head = getattr(rule, "head", None)
            atom = getattr(head, "atom", None)
            ast_type = getattr(atom, "ast_type", None)
            if ast_type != ASTType.BooleanConstant:
                return True
        return False


class ProgramReifier(DependencyCollector):

    def __init__(self,
                 rule_nr=1,
                 h="h",
                 h_showTerm="h_showTerm",
                 model="model",
                 get_conflict_free_variable=lambda s: s,
                 clear_temp_names=lambda: None,
                 conflict_free_showTerm: str = "ShowTerm"):
        self.rule_nr = rule_nr
        self.h = h
        self.h_showTerm = h_showTerm
        self.model = model
        self.get_conflict_free_variable = get_conflict_free_variable
        self.clear_temp_names = clear_temp_names
        self.conflict_free_showTerm = conflict_free_showTerm

    def _nest_rule_head_in_h_with_explanation_tuple(
        self,
        loc: ast.Location,
        dependant: ast.Literal, # type: ignore
        conditions: List[ast.Literal], # type: ignore
        reasons: List[ast.Literal], # type: ignore
        use_h_showTerm: bool = False,
    ):
        """
        In: H :- B.
        Out: h(0, H, pos_atoms(B)),
        where pos_atoms(B) is a tuple of all positive Symbolic Atoms in B.
        """
        loc_fun = ast.Function(loc, str(self.rule_nr), [], False)
        loc_atm = ast.SymbolicAtom(loc_fun)
        loc_lit = ast.Literal(loc, ast.Sign.NoSign, loc_atm)
        for literal in conditions:
            if literal.atom.ast_type == ASTType.SymbolicAtom:
                reasons.append(literal.atom)
        reasons.reverse()
        reasons = [r for i, r in enumerate(reasons) if r not in reasons[:i]]
        reason_fun = ast.Function(loc, "", reasons, 0)
        reason_lit = ast.Literal(loc, ast.Sign.NoSign, reason_fun)

        h_attribute = self.h_showTerm if use_h_showTerm else self.h

        return [
            ast.Function(loc, h_attribute, [loc_lit, dependant, reason_lit], 0)
        ]

    def post_rule_creation(self):
        self.clear_temp_names()

    def visit_Rule(self, rule: ast.Rule) -> List[AST]: # type: ignore
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
        _ = self.visit(rule.head, deps=deps, in_head=True)

        if is_fact(rule, deps) or is_constraint(rule):
            return [rule]
        if not deps:
            # if it's a "simple head"
            deps[rule.head] = []
        new_rules: List[ast.Rule] = [] # type: ignore
        for dependant, conditions in deps.items():
            if has_an_interval(dependant):
                # replace dependant with variable: e.g. (1..3) -> X
                variables = [
                    ast.Variable(loc, self.get_conflict_free_variable())
                    if arg.ast_type == ASTType.Interval else arg
                    for arg in dependant.atom.symbol.arguments
                ]
                symbol = ast.SymbolicAtom(
                    ast.Function(loc, dependant.atom.symbol.name, variables,
                                 False))
                dependant = ast.Literal(loc, ast.Sign.NoSign, symbol)

            new_body: List[ast.Literal] = [] # type: ignore
            reason_literals: List[ast.Literal] = [] # type: ignore
            _ = self.visit_sequence(
                rule.body,
                reasons=reason_literals,
                new_body=new_body,
                rename_variables=False,
            )
            new_head_s = self._nest_rule_head_in_h_with_explanation_tuple(
                rule.location, dependant, conditions, reason_literals)

            new_body.insert(0, dependant)
            new_body.extend(conditions)
            # Remove duplicates but preserve order
            new_body = [
                x for i, x in enumerate(new_body) if x not in new_body[:i]
            ]
            # rename variables inside body aggregates
            new_body = list(
                self.visit_sequence(cast(ast.ASTSequence, new_body),
                                    rename_variables=True))
            new_rules.extend([
                ast.Rule(rule.location, new_head, new_body)
                for new_head in new_head_s
            ])
            self.post_rule_creation()

        return new_rules

    def visit_ShowTerm(self, showTerm: ast.ShowTerm):  # type: ignore
        # Embed the head
        deps = defaultdict(list)
        loc = showTerm.location
        _ = self.visit(showTerm.term, deps=deps, in_head=True)

        new_rules = []
        if has_an_interval(showTerm.term):
            # replace dependant with variable: e.g. (1..3) -> X
            variables = [
                ast.Variable(loc, self.get_conflict_free_variable())
                if arg.ast_type == ASTType.Interval else arg
                for arg in showTerm.term.atom.symbol.arguments
            ]
            symbol = ast.SymbolicAtom(
                ast.Function(loc, showTerm.term.atom.symbol.name, variables,
                             False))
            showTerm.term = ast.Literal(loc, ast.Sign.NoSign, symbol)

        new_body_literals: List[AST] = []
        reason_literals: List[AST] = []
        _ = self.visit_sequence(
            showTerm.body,
            reasons=reason_literals,
            new_body=new_body_literals,
            rename_variables=False,
        )
        new_head_s = self._nest_rule_head_in_h_with_explanation_tuple(
            showTerm.location, showTerm.term, [], reason_literals, True)

        new_body_literals.insert(
            0,
            ast.Literal(
                loc, ast.Sign.NoSign,
                ast.Function(loc, self.conflict_free_showTerm, [showTerm.term],
                             0)))
        # Remove duplicates but preserve order
        new_body_literals = [
            x for i, x in enumerate(new_body_literals)
            if x not in new_body_literals[:i]
        ]
        # rename variables inside body aggregates
        new_body_literals = list(
            self.visit_sequence(cast(ast.ASTSequence, new_body_literals),
                                rename_variables=True))
        new_rules.extend([
            ast.Rule(showTerm.location, new_head, new_body_literals)
            for new_head in new_head_s
        ])
        self.post_rule_creation()

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
    parse_string(program,
                 lambda rule: register_rules(visitor.visit(rule), rulez))
    return rulez


def reify(transformation: Transformation, **kwargs):
    visitor = ProgramReifier(transformation.id, **kwargs)
    result: List[AST] = []
    for rule in transformation.rules:
        result.extend(cast(Iterable[AST], visitor.visit(rule)))
    return result


def reify_list(transformations: Iterable[Transformation],
               **kwargs) -> List[AST]:
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
            if arg.ast_type == ASTType.Interval:
                return True
    except AttributeError:
        return False
    return False
