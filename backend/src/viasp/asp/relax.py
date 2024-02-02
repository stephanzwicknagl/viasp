from clingo.ast import (AST, Transformer, SymbolicTerm, Function, Literal,
                    SymbolicAtom, parse_string, Sign)
from clingo import Function as ClingoFunction, ast
from .utils import is_constraint
from typing import List


class TermRelaxer(Transformer):
    """
    Transformer for visiting variables and collecting them. 
    If the variable is inside of an unwanted literal, it isn't collected.
    """

    def visit_Variable(
            self,
            Variable: ast.Variable,  # type: ignore
            **kwargs) -> AST:
        """
        Visit a variable. Add it to the collector via the callback method adder in kwargs.
        """
        kwargs.get("adder", lambda x: None)(Variable)
        return Variable

    def visit_Literal(
            self,
            Literal: ast.Literal,  # type: ignore
            **kwargs) -> AST:
        """
        Visit a literal. If it is not positive, update the collect_bool to False.
        """
        if Literal.sign != Sign.NoSign:
            return Literal
        return Literal.update(**self.visit_children(Literal, **kwargs))

    def visit_ConditionalLiteral(
            self,
            ConditionalLiteral: ast.ConditionalLiteral,  # type: ignore
            **kwargs) -> AST:
        return ConditionalLiteral

    def visit_BooleanConstant(
            self,
            BooleanConstant: ast.BooleanConstant,  # type: ignore
            **kwargs) -> AST:
        return BooleanConstant

    def visit_BodyAggregate(
            self,
            BodyAggregate: ast.BodyAggregate,  # type: ignore
            **kwargs) -> AST:
        return BodyAggregate

    def visit_TheoryAtom(
            self,
            TheoryAtom: ast.TheoryAtom,  # type: ignore
            **kwargs) -> AST:
        return TheoryAtom


class ProgramRelaxer(TermRelaxer):
    """
    Transformer class for modifying rules in a program.
    """

    def __init__(self, *args, **kwargs):
        self.head_name: str = kwargs.get("head_name", "unsat")
        self.collect_variables: bool = kwargs.get("collect_variables", True)
        self.constraint_counter: int = 1

    def visit_Rule(self, rule: ast.Rule) -> AST: # type: ignore
        """
        Visit a rule. If it is an integrity constraint, make a new head literal.
        New head literals are either of the form
        unsat(R) or unsat(R, T), where R is the variable identifying 
        the integrity constraint and T is a tuple of variables. It depends
        on whether the relaxer collects variables or not.
        If it is not an integrity constraint, return the rule unchanged.

        :param rule: The rule being visited.
        :return: The modified rule.
        """
        if is_constraint(rule):
            location = rule.head.location
            args = [SymbolicTerm(location, ClingoFunction(f'r{self.constraint_counter}', [], True))]
            self.constraint_counter += 1

            if self.collect_variables:
                variables: List[AST] = []
                _ = self.visit_sequence(rule.body, adder=variables.append)
                variables = [v for i,v in enumerate(variables) if v not in variables[:i]]
                if variables != []:
                    args.append(Function(location, '', variables, 0))

            rule.head = Literal(location = location,
                        sign = 0,
                        atom = SymbolicAtom(Function(location, self.head_name, args, 0)))
        return rule


def relax_constraints(relaxer: ProgramRelaxer, program: str) -> List[AST]:
    """
    Relax constraints in a program and add minimization statement.
    The minimization statement changes depending on whether the
    relaxer collects variables or not.
    Returns the relaxed program as a list of AST.

    :param relaxer: An instance of the relaxer class.
    :param program: The program to relax..
    :return: The relaxed program as a list of AST.
    """
    # Add minimization statement
    program += f"\n:~ {relaxer.head_name}(R,T).[1,R,T]" if \
                    relaxer.collect_variables else f"\n:~ {relaxer.head_name}(R).[1,R]"
    relaxed_program: List[AST] = []
    parse_string(program, lambda stm: relaxed_program.append(relaxer.visit(stm)))
    return relaxed_program
