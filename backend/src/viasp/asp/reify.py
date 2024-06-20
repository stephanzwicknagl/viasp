from collections import defaultdict
from typing import Dict, List, Tuple, Iterable, Set, Collection, Any, Union, Sequence, Optional, cast

import clingo
import networkx as nx
from clingo import ast, Symbol, Number
from clingo.ast import (
    Transformer,
    parse_string,
    ASTType,
    AST,
    Literal as astLiteral,
    SymbolicAtom as astSymbolicAtom
)
from viasp.shared.util import hash_transformation_rules

from .utils import find_index_mapping_for_adjacent_topological_sorts, is_constraint, merge_constraints, topological_sort, filter_body_aggregates
from ..asp.utils import merge_cycles, remove_loops
from viasp.asp.ast_types import (
    SUPPORTED_TYPES,
    ARITH_TYPES,
    UNSUPPORTED_TYPES,
)
from ..shared.model import Transformation, TransformationError, FailedReason, RuleContainer
from ..shared.simple_logging import error


def is_fact(rule, dependencies):
    return len(rule.body) == 0 and not len(dependencies)

def make_signature_from_terms(term) -> Optional[Tuple[str, int]]:
    if term.ast_type == ASTType.SymbolicTerm:
        return term.symbol.name, 0
    elif term.ast_type == ASTType.Variable:
        return (term.name, 0)
    elif term.ast_type == ASTType.UnaryOperation:
        return make_signature_from_terms(term.argument)
    elif term.ast_type == ASTType.BinaryOperation:
        return None
    elif term.ast_type == ASTType.Interval:
        return None
    elif term.ast_type == ASTType.Function:
        return (term.name, len(term.arguments))
    elif term.ast_type == ASTType.Pool:
        return make_signature_from_terms(term.arguments[0])
    raise ValueError(f"Could not make signature of {term}.")

def make_signature(ast: Union[ast.Literal, ast.ConditionalLiteral]) -> Optional[Tuple[str, int]]:  # type: ignore
    """
    Is used to create a signature for a literal or conditional literal for placing it in the dependency graph.
    `None` is returned for types of literals that are unsupported or neglected in the dependency graph.
    """
    if ast.ast_type == ASTType.Literal:
        atom = ast.atom
    else:
        return None

    if atom.ast_type == ASTType.BodyAggregate:
        return None
    elif atom.ast_type == ASTType.BooleanConstant:
        return None
    elif atom.ast_type == ASTType.Comparison:
        return None
    elif atom.ast_type == ASTType.Aggregate:
        return None
    elif atom.ast_type == ASTType.TheoryAtom:
        raise ValueError(f"Could not make signature of {ast}.")
    elif atom.ast_type == ASTType.SymbolicAtom:
        term = atom.symbol
        return make_signature_from_terms(term)

    raise ValueError(f"Could not make signature of {ast}, {ast.ast_type}.")


def filter_body_arithmetic(elem: ast.Literal):  # type: ignore
    elem_ast_type = getattr(getattr(elem, "atom", ""), "ast_type", None)
    return elem_ast_type not in ARITH_TYPES


class FilteredTransformer(Transformer):

    def __init__(self, accepted=None, forbidden=None, warning=None):
        if accepted is None:
            accepted = SUPPORTED_TYPES
        if forbidden is None:
            forbidden = UNSUPPORTED_TYPES
        self._accepted: Collection[ASTType] = accepted
        self._forbidden: Collection[ASTType] = forbidden
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
        attr = "visit_" + str(ast.ast_type).replace("ASTType.", "")
        if hasattr(self, attr):
            return getattr(self, attr)(ast, *args, **kwargs)
        return ast.update(**self.visit_children(ast, *args, **kwargs))


class DependencyCollector(Transformer):

    def __init__(self, **kwargs):
        self.compound_atoms_types: List = [
            ASTType.Aggregate, ASTType.BodyAggregate, ASTType.Comparison
        ]
        self.in_analyzer = kwargs.get("in_analyzer", False)

    def visit_ConditionalLiteral(
            self,
            conditional_literal: ast.ConditionalLiteral,  # type: ignore
            **kwargs: Any) -> AST:
        deps = kwargs.get("deps", {})
        in_head = kwargs.get("in_head", False)
        in_aggregate = kwargs.get("in_aggregate", False)
        in_analyzer = kwargs.get("in_analyzer", False)
        conditions: List[AST] = kwargs.get("conditions", [])

        if in_head:
            # collect deps for choice rules
            deps[conditional_literal.literal] = ([], [])
            for condition in conditional_literal.condition:
                deps[conditional_literal.literal][0].append(condition)
        if (not in_aggregate and not in_analyzer):
            # add simple Cond.Literals from rule body to justifier rule body
            conditions.append(conditional_literal)
        kwargs.update({"in_aggregate": True})
        return conditional_literal.update(
            **self.visit_children(conditional_literal, **kwargs))

    def visit_Literal(
            self,
            literal: ast.Literal,  # type: ignore
            **kwargs: Any) -> AST:
        conditions: List[AST] = kwargs.get("conditions", [])
        positive_conditions: List[AST] = kwargs.get("positive_conditions", [])
        in_aggregate = kwargs.get("in_aggregate", False)

        if (self.in_analyzer
                and literal.atom.ast_type not in self.compound_atoms_types):
            # all non-compound Literals in the rule body are conditions of the rule
            conditions.append(literal)
            if literal.sign == ast.Sign.NoSign and not in_aggregate:
                positive_conditions.append(literal)
        if (not self.in_analyzer and not in_aggregate):
            # add all Literals outside of aggregates from rule body to justifier rule body
            conditions.append(literal)
        return literal.update(**self.visit_children(literal, **kwargs))

    def visit_Aggregate(
            self,
            aggregate: ast.Aggregate,  # type: ignore
            **kwargs: Any) -> AST:
        kwargs.update({"in_aggregate": True})
        return aggregate.update(**self.visit_children(aggregate, **kwargs))

    def visit_BodyAggregate(
            self,
            body_aggregate: ast.BodyAggregate,  # type: ignore
            **kwargs: Any) -> AST:
        kwargs.update({"in_aggregate": True})
        return body_aggregate.update(
            **self.visit_children(body_aggregate, **kwargs))


class ProgramAnalyzer(DependencyCollector, FilteredTransformer):
    """
    Receives a ASP program and finds it's dependencies within, can sort a program by it's dependencies.
    """

    def __init__(self, dependants: Optional[Dict[Tuple[str, int], Set[ast.Rule]]] = None,  # type: ignore
                    conditions: Optional[Dict[Tuple[str, int], Set[ast.Rule]]] = None,  # type: ignore
                 dependency_graph: Optional[nx.DiGraph] = None):
        DependencyCollector.__init__(self, in_analyzer=True)
        FilteredTransformer.__init__(self)
        self.dependants: Dict[Tuple[str, int],
                              Set[ast.Rule]] = defaultdict(set)  # type: ignore
        self.conditions: Dict[Tuple[str, int],
                              Set[ast.Rule]] = defaultdict(set)  # type: ignore
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
        self.dependency_graph: Optional[nx.DiGraph] = dependency_graph

    def _get_conflict_free_version_of_name(self, name: str) -> str:
        anti_candidates = self.names.union(self.temp_names)
        current_best = name
        for i in range(10):
            for _ in range(10):
                if current_best in anti_candidates:
                    current_best = f"{current_best}_"
                else:
                    return current_best
            current_best = f"{name}{i}"
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

    def get_conflict_free_variable(self, name: str = "X"):
        """
        For use in the replacement of Intervals.
        By a new conflict free (unique) variable.
        The new variable is added to the set of known variables.
        """
        new_var = self._get_conflict_free_version_of_name(name)
        self.temp_names.add(new_var)
        return new_var

    def get_conflict_free_iterindex(self):
        """
        For use in generation of subgraphs at recursive
        transformations.
        """
        return self._get_conflict_free_version_of_name("n")

    def get_conflict_free_derivable(self):
        """
        For use in generation of subgraphs at recursive
        transformations.
        """
        return self._get_conflict_free_version_of_name("derivable")

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

    def register_rule_conditions(
            self,
            rule: ast.Rule,  # type: ignore
            conditions: List[ast.Literal]) -> None:  # type: ignore
        for c in conditions:
            c_sig = make_signature(c)
            if c_sig is not None:
                self.conditions[c_sig].add(rule)

    def register_rule_dependencies(
        self,
        rule: ast.Rule,  # type: ignore
        deps: Dict[
            ast.Literal,  # type: ignore
            List[ast.Literal]]  # type: ignore
    ) -> None:
        for (cond, pos_cond) in deps.values():
            for c in filter(filter_body_arithmetic, cond):
                c_sig = make_signature(c)
                if c_sig is not None:
                    self.conditions[c_sig].add(rule)
            for c in filter(filter_body_arithmetic, pos_cond):
                c_sig = make_signature(c)
                if c_sig is not None:
                    self.positive_conditions[c_sig].add(rule)

        for v in deps.keys():
            if v.ast_type == ASTType.Literal and v.atom.ast_type != ASTType.BooleanConstant:
                v_sig = make_signature(v)
                if v_sig is not None:
                    self.dependants[v_sig].add(rule)

    def get_body_aggregate_elements(self, body: Sequence[AST]) -> List[AST]:
        body_aggregate_elements: List[AST] = []
        for elem in body:
            self.visit(elem, body_aggregate_elements=body_aggregate_elements)
        return body_aggregate_elements

    def process_body(self, head, body, deps, in_analyzer=True):
        if not len(deps) and len(body):
            deps[head] = ([], [])
        for _, (cond, pos_cond) in deps.items():
            self.visit_sequence(body,
                                conditions=cond,
                                positive_conditions=pos_cond,
                                in_analyzer=in_analyzer)

    def register_dependencies_and_append_rule(self, rule, deps):
        self.register_rule_dependencies(rule, deps)
        self.rules.append(rule)

    def visit_Rule(self, rule: ast.Rule):  # type: ignore
        deps = defaultdict(tuple)
        _ = self.visit(rule.head, deps=deps, in_head=True)
        self.process_body(rule.head, rule.body, deps)
        self.register_dependencies_and_append_rule(rule, deps)
        if is_fact(rule, deps):
            self.facts.add(rule.head)

    def visit_ShowTerm(self, showTerm: ast.ShowTerm):  # type: ignore
        deps = defaultdict(tuple)
        _ = self.visit(showTerm.term, deps=deps, in_head=True)
        head_literal = ast.Literal(showTerm.location, ast.Sign.NoSign,
                                   ast.SymbolicAtom(showTerm.term))
        self.process_body(head_literal, showTerm.body, deps)
        self.register_dependencies_and_append_rule(showTerm, deps)

    def visit_Minimize(self, minimize: ast.Minimize):  # type: ignore
        deps = defaultdict(tuple)
        true_head_literal = ast.Literal(minimize.location, ast.Sign.NoSign,
                                        ast.BooleanConstant(1))
        deps[true_head_literal] = ([], [])
        self.process_body(true_head_literal, minimize.body, deps)
        self.register_dependencies_and_append_rule(minimize, deps)

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
        from viasp.server.database import GraphAccessor, get_or_create_encoding_id
        GraphAccessor().save_program(program, get_or_create_encoding_id())
        parse_string(program, lambda rule: self.visit(rule) and None)
        sorted_program = self.primary_sort_program_by_dependencies()
        return [
            Transformation(i, prg)
            for i, prg in enumerate(sorted_program)
        ]

    def get_sort_program_and_graph(
            self, program: str) -> Tuple[List[RuleContainer], nx.DiGraph]:
        from viasp.server.database import GraphAccessor, get_or_create_encoding_id
        GraphAccessor().save_program(program, get_or_create_encoding_id())
        parse_string(program, lambda rule: self.visit(rule) and None)
        sorted_programs = self.primary_sort_program_by_dependencies()
        return sorted_programs, self.make_dependency_graph(
            self.dependants, self.conditions)

    def get_sorted_program(self) -> List[Transformation]:
        sorted_program = self.primary_sort_program_by_dependencies()
        return self.make_transformations_from_sorted_program(sorted_program)

    def make_transformations_from_sorted_program(
        self, sorted_program: List[RuleContainer]  # type: ignore
    ) -> List[Transformation]:
        adjacency_index_mapping = self.get_index_mapping_for_adjacent_topological_sorts(
            sorted_program)
        transformations = [
            Transformation(i, prg, adjacency_index_mapping[i])
            for i, prg in enumerate(sorted_program)
        ]
        transformations.sort(key=lambda t: t.id)
        return transformations

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
                g.add_node(RuleContainer(tuple([dep])))
        for deps in body_dependencies.values():
            for dep in deps:
                g.add_node(RuleContainer(tuple([dep])))

        for head_signature, rules_with_head in head_dependencies.items():
            dependent_rules = body_dependencies.get(head_signature, [])
            for parent_rule in rules_with_head:
                for dependent_rule in dependent_rules:
                    g.add_edge(RuleContainer(tuple([parent_rule])), RuleContainer(tuple([dependent_rule])))

        return g

    def primary_sort_program_by_dependencies(
            self) -> List[RuleContainer]:
        graph = self.make_dependency_graph(self.dependants, self.conditions)
        graph = merge_constraints(graph)
        graph, _ = merge_cycles(graph)
        graph, _ = remove_loops(graph)
        self.dependency_graph = cast(nx.DiGraph, graph.copy())
        sorted_program = topological_sort(graph, self.rules)
        return sorted_program

    def get_index_mapping_for_adjacent_topological_sorts(
        self,
        sorted_program: List[RuleContainer]
    ) -> Dict[int, Dict[str, int]]:
        if self.dependency_graph is None:
            raise ValueError(
                "Dependency graph has not been created yet. Call primary_sort_program_by_dependencies first."
            )
        return find_index_mapping_for_adjacent_topological_sorts(
            self.dependency_graph, sorted_program)

    def check_positive_recursion(self) -> Set[str]:
        positive_dependency_graph = self.make_dependency_graph(self.dependants,
                                           self.positive_conditions)
        positive_dependency_graph = merge_constraints(positive_dependency_graph)
        positive_dependency_graph_withput_cycles, where1 = merge_cycles(positive_dependency_graph)
        _, where2 = remove_loops(positive_dependency_graph_withput_cycles)

        recursion_rules = set()
        for t in where1.union(where2):
            if any(not is_constraint(r) for r in t.ast):
                recursion_rules.add(hash_transformation_rules(t.ast))
        return recursion_rules

    def should_include_recursive_set(self, recursive_tuple: Tuple[AST, ...]):
        """
        Drop the set of integrity constraints from the recursive set.
        """
        for rule in recursive_tuple:
            head = getattr(rule, "head", None)
            atom = getattr(head, "atom", None)
            ast_type = getattr(atom, "ast_type", None)
            if ast_type == ASTType.BooleanConstant:
                return False
        return True


class ProgramReifier(DependencyCollector):

    def __init__(self,
                 rule_nr=1,
                 h="h",
                 h_showTerm="h_showTerm",
                 model="model",
                 get_conflict_free_variable=lambda s: s,
                 clear_temp_names=lambda: None,
                 conflict_free_showTerm: str = "showTerm"):
        self.rule_nr = rule_nr
        self.h = h
        self.h_showTerm = h_showTerm
        self.model = model
        self.get_conflict_free_variable = get_conflict_free_variable
        self.clear_temp_names = clear_temp_names
        self.conflict_free_showTerm = conflict_free_showTerm
        super().__init__(in_analyzer=False)

    def make_loc_lit(self, loc: ast.Location) -> ast.Literal:  # type: ignore
        loc_fun = ast.Function(loc, str(self.rule_nr), [], False)
        loc_atm = ast.SymbolicAtom(loc_fun)
        return ast.Literal(loc, ast.Sign.NoSign, loc_atm)

    def _nest_rule_head_in_h_with_explanation_tuple(
        self,
        loc: ast.Location,
        dependant: ast.Literal,  # type: ignore
        conditions: List[ast.Literal],  # type: ignore
        use_h_showTerm: bool = False,
    ):
        """
        In: H :- B.
        Out: h(0, H, pos_atoms(B)),
        where pos_atoms(B) is a tuple of all positive Symbolic Atoms in B.
        """
        reasons: List[ast.Literal] = []  # type: ignore

        loc_lit = self.make_loc_lit(loc)
        for literal in conditions:
            if hasattr(literal, "sign") and \
                literal.sign == ast.Sign.NoSign and \
                hasattr(literal, "atom") and \
                hasattr(literal.atom, "ast_type") and \
               literal.atom.ast_type == ASTType.SymbolicAtom:
                reasons.append(literal.atom)
        reasons.reverse()
        reasons = [r for i, r in enumerate(reasons) if r not in reasons[:i]]
        reason_fun = ast.Function(loc, "",
                                  [r for r in reasons if r is not None], 0)
        reason_lit = ast.Literal(loc, ast.Sign.NoSign, reason_fun)

        h_attribute = self.h_showTerm if use_h_showTerm else self.h

        return [
            ast.Function(loc, h_attribute, [loc_lit, dependant, reason_lit], 0)
        ]

    def post_rule_creation(self):
        self.clear_temp_names()

    def process_dependant_intervals(
            self, loc: ast.Location,
            dependant: Union[ast.Literal, ast.Function]):  # type: ignore
        if dependant.ast_type == ASTType.Function:
            dependant = ast.Literal(loc, ast.Sign.NoSign,
                                    ast.SymbolicAtom(dependant))
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
        return dependant

    def visit_Rule(self, rule: ast.Rule) -> List[AST]:  # type: ignore
        """
        Reify a rule into a set of new rules.
        Also replaces any interval in the head with a variable and adds it to the body.
        In: H :- B.
        Out: h(0, H, pos_atoms(B)) :- H, B.
        where pos_atoms(B), reasons for H, is a tuple of all positive Symbolic Atoms in B.


        :param rule: The rule to reify
        :return: A list of new rules"""
        # Embed the head
        deps = defaultdict(tuple)
        loc = rule.location
        _ = self.visit(rule.head, deps=deps, in_head=True)

        if is_fact(rule, deps) or is_constraint(rule):
            return [rule]
        if not deps:
            # if it's a "simple head"
            deps[rule.head] = ([], [])
        new_rules: List[ast.Rule] = []  # type: ignore
        for dependant, (conditions, _) in deps.items():
            dependant = self.process_dependant_intervals(loc, dependant)

            _ = self.visit_sequence(
                rule.body,
                conditions=conditions,
            )
            self.replace_anon_variables(conditions)
            new_head_s = self._nest_rule_head_in_h_with_explanation_tuple(
                rule.location, dependant, conditions)

            conditions.insert(0, dependant)
            # Remove duplicates but preserve order
            conditions = [
                x for i, x in enumerate(conditions) if x not in conditions[:i]
            ]
            new_rules.extend([
                ast.Rule(rule.location, new_head, conditions)
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
        showTerm.term = self.process_dependant_intervals(loc, showTerm.term)

        conditions: List[AST] = []
        _ = self.visit_sequence(
            showTerm.body,
            conditions=conditions,
        )
        self.replace_anon_variables(conditions)
        new_head_s = self._nest_rule_head_in_h_with_explanation_tuple(
            showTerm.location, showTerm.term, conditions, True)

        conditions.insert(
            0,
            ast.Literal(
                loc, ast.Sign.NoSign,
                ast.Function(loc, self.conflict_free_showTerm, [showTerm.term],
                             0)))
        # Remove duplicates but preserve order
        conditions = [
            x for i, x in enumerate(conditions) if x not in conditions[:i]
        ]
        new_rules.extend([
            ast.Rule(showTerm.location, new_head, conditions)
            for new_head in new_head_s
        ])
        self.post_rule_creation()

        return new_rules

    def visit_Minimize(self, minimize: ast.Minimize):  # type: ignore
        return [minimize]

    def replace_anon_variables(
            self, literals: List[ast.Literal]) -> None:  # type: ignore
        """
        Replaces all anonymous variables in the literals with a new variable.
        """
        for l in literals:
            try:
                if l.ast_type == ASTType.Literal and \
                    l.sign == ast.Sign.NoSign:
                    for arg in l.atom.symbol.arguments:
                        if arg.ast_type == ASTType.Variable and arg.name == "_":
                            arg.name = self.get_conflict_free_variable(
                                f"ANON_{arg.location.begin.line}{arg.location.begin.column}_{arg.location.end.line}{arg.location.end.column}_"
                            )
            except AttributeError:
                continue


class LiteralWrapper(Transformer):

    def __init__(self, *args, **kwargs):
        self.wrap_str: str = kwargs.pop("wrap_str", "model")
        self.no_wrap_types: List[ASTType] = [
            ASTType.Aggregate, ASTType.BodyAggregate, ASTType.Comparison,
            ASTType.BooleanConstant
        ]
        super().__init__(*args, **kwargs)

    def visit_Literal(self,
                      literal: ast.Literal) -> ast.Literal:  # type: ignore
        if literal.sign != ast.Sign.NoSign:
            return None
        if literal.atom.ast_type in self.no_wrap_types:
            return literal.update(**self.visit_children(literal))
        wrap_fun = ast.Function(literal.location, self.wrap_str, [literal], 0)
        wrap_atm = ast.SymbolicAtom(wrap_fun)
        return ast.Literal(literal.location, ast.Sign.NoSign, wrap_atm)


class ProgramReifierForRecursions(ProgramReifier):

    def __init__(self, *args, **kwargs):
        self.model_str: str = kwargs.pop("conflict_free_model", "model")
        self.n_str: str = kwargs.pop("conflict_free_iterindex", "n")
        self.derivable_str: str = kwargs.pop("conflict_free_derivable", "derivable")
        super().__init__(*args, **kwargs)

    def visit_Rule(self, rule: ast.Rule) -> List[AST]:  # type: ignore
        deps = defaultdict(tuple)
        loc = cast(ast.Location, rule.location)
        _ = self.visit(rule.head, deps=deps, in_head=True)

        if is_fact(rule, deps) or is_constraint(rule):
            return [rule]
        if not deps:
            # if it's a "simple head"
            deps[rule.head] = ([], [])
        new_rules: List[ast.Rule] = []  # type: ignore
        for dependant, (conditions, _) in deps.items():
            dependant = self.process_dependant_intervals(loc, dependant)

            _ = self.visit_sequence(
                rule.body,
                conditions=conditions,
            )

            self.replace_anon_variables(conditions)
            new_head_s = self._nest_rule_head_in_h_with_explanation_tuple(
                rule.location, dependant, conditions)

            # Remove duplicates but preserve order
            conditions = [
                x for i, x in enumerate(conditions) if x not in conditions[:i]
            ]

            # Wrap in model function
            wrapper = LiteralWrapper(wrap_str=self.model_str)
            conditions = [wrapper.visit(c) for c in conditions]
            conditions = [c for c in conditions if c is not None]

            # Append dependant (wrapped, negated)
            dep_fun = ast.Function(loc, self.model_str, [dependant], 0)
            dep_atm = ast.SymbolicAtom(dep_fun)
            conditions.append(ast.Literal(loc, ast.Sign.Negation, dep_atm))

            # # Append dependant wrapped in derivable
            derivable_fun = ast.Function(loc, self.derivable_str, [dependant], 1)
            derivable_comp = ast.Comparison(derivable_fun, [ast.Guard(5, ast.SymbolicTerm(loc, Number(1)))])
            conditions.append(ast.Literal(loc, ast.Sign.NoSign, derivable_comp))

            new_rules.extend([
                ast.Rule(rule.location, new_head, conditions)
                for new_head in new_head_s
            ])
            self.post_rule_creation()

        return new_rules

    def make_loc_lit(self, loc: ast.Location) -> ast.Literal:  # type: ignore
        loc_fun = ast.Function(loc, self.n_str, [], False)
        loc_atm = ast.SymbolicAtom(loc_fun)
        return ast.Literal(loc, ast.Sign.NoSign, loc_atm)


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
    for rule in transformation.rules.ast:
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


def has_an_interval(literal: ast.Literal) -> bool:  # type: ignore
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


def reify_recursion_transformation(transformation: Transformation,
                                   **kwargs) -> List[AST]:
    visitor = ProgramReifierForRecursions(**kwargs)
    result: List[AST] = []
    for rule in transformation.rules.ast:
        result.extend(cast(Iterable[AST], visitor.visit(rule)))
    return result


class LiteralsCollector(Transformer):

    def visit_Literal(
            self,
            literal: ast.Literal,  # type: ignore
            **kwargs: Any) -> AST:
        literals: List[AST] = kwargs.get("literals", [])
        literals.append(literal)
        return literal.update(**self.visit_children(literal, **kwargs))


def collect_literals(program: str):
    visitor = LiteralsCollector()
    literals = []
    parse_string(program,
                 lambda rule: visitor.visit(rule, literals=literals) and None)
    return literals
