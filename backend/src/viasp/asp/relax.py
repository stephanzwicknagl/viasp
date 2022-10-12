from typing import List, Set
from clingo.ast import (AST, SymbolicTerm, Function, Literal,
                    SymbolicAtom, ASTSequence, parse_string, Sign)

from clingo import Function as ClingoFunction
from .utils import is_constraint

class Relaxer:
    def visit_children(self, x, *args, **kwargs):
        for key in x.child_keys:
            setattr(x, key, self.visit(getattr(x, key), *args, **kwargs))
        return x

    def visit(self, x, *args, **kwargs):
        if isinstance(x, AST):
            attr = 'visit_' + str(x.ast_type).replace('ASTType.', '')
            if hasattr(self, attr):
                return getattr(self, attr)(x, *args, **kwargs)
            else:
                return self.visit_children(x, *args, **kwargs)
        elif isinstance(x, list):
            return [self.visit(y, *args, **kwargs) for y in x]
        elif isinstance(x, ASTSequence):
            return [self.visit(y, *args, **kwargs) for y in x]
        elif x is None:
            return x
        else:
            raise TypeError("unexpected type")


class TermRelaxer(Relaxer):
    """
        Transformer for visiting a term and collecting variables for the head.
        Only Variables from positive literals, comparisons and guards are collected.
    """
    def __init__(self):
        self.collector: Set[AST] = set()

    def visit_Literal(self, literal):
        """
            Visit a literal. If it is positive or double negation, visit its children.
        """
        if literal.sign != Sign.Negation:
            _ = self.visit_children(literal)
        return literal

    def visit_Variable(self, term):
        """
            Visit a variable. Add it to the collector.
        """
        self.collector.add(term)
        return term

    def visit_BodyAggregateElement(self, term):
        """
            Visit a body aggregate element. Do not visit its children.
        """
        return term

    def empty_collector(self):
        self.collector = set()


class ProgramRelaxer(Relaxer):
    """
        transformer for ASP programs. Relaxes constraints by adding a new rule head.
        Only rules are modified, but all statement types are visited to return a complete program.
    """

    def __init__(self, *args, **kwargs):#head_name="unsat", get_variables=True):
        if "head_name" in kwargs:
            self.head_name: str = kwargs["head_name"]
        else:
            self.head_name: str = "unsat"
        if "get_variables" in kwargs:
            self.collect_variables: bool = kwargs["collect_variables"]
        else:
            self.collect_variables: bool = True
        self.relaxed_program: List[AST] = []
        self.term_relaxer = TermRelaxer()
        self.constraint_counter: int = 1

    def visit_Rule(self, rule):
        """
            Visit a rule. If it is a constraint, relax it.
        """
        if is_constraint(rule):
            args = self._get_variables(rule)
            # create new rule head:
            rule.head = self._make_head_literal(rule, args)
        self._register_relaxed_program(rule)
        return rule

    def visit_Program(self, prg):
        """
            Visit a program.
        """
        self._register_relaxed_program(prg)
        return prg

    def relax_constraints(self, program: str) -> list[str]:
        """
            Relax constraints in a program and add minimization statement.

            E.g.: :- a(X). -> unsat(r1,(X,)):- a(X).:~unsat(R,T).[1,R,T]
        """
        parse_string(program, lambda statement: self.visit(statement))
        stringified = list(map(str, self.relaxed_program))

        stringified.append(f":~ {self.head_name}(R,T).[1,R,T]" if
                    self.collect_variables else f":~ {self.head_name}(R).[1,R]")
        return stringified

    def _register_relaxed_program(self, rule: AST):
        self.relaxed_program.append(rule)

    def _make_head_literal(self, rule: AST, inner_args: Set[AST]) -> AST:
        location = rule.head.location
        args = [SymbolicTerm(location, ClingoFunction(f'r{self._constraint_number()}', [], True))]
        if inner_args:
            args.append(Function(location, '', list(inner_args),0))
        atom = SymbolicAtom(Function(location, self.head_name, args, 0))
        return Literal(location, 0, atom)

    def _constraint_number(self) -> int:
        i = self.constraint_counter
        self.constraint_counter += 1
        return i

    def _get_variables(self, rule: AST):
        if not self.collect_variables:
            return set()
        # reset the arg collector
        self.term_relaxer.empty_collector()
        # get arguments of body:
        for term in rule.body:
            _ = self.term_relaxer.visit(term)
        return self.term_relaxer.collector
