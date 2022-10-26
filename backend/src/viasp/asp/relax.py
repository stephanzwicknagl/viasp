from clingo.ast import (AST, Transformer, SymbolicTerm, Function, Literal,
                    SymbolicAtom, parse_string, Sign)
from clingo import Function as ClingoFunction
from .utils import is_constraint
from typing import List

class TermRelaxer(Transformer):
    """ Transformer for visiting variables and collecting them.
    """
    def visit_Variable(self, Variable: AST, **kwargs) -> AST:
        """
            Visit a variable. Add it to the collector via the callback method adder in kwargs.
        """
        kwargs.get("adder", None)(Variable)
        return Variable


class ProgramRelaxer():
    """ Class for modifying rules in a program.
    """

    def __init__(self, *args, **kwargs):
        self.head_name: str = kwargs["head_name"] if "head_name" in kwargs else "unsat"
        self.collect_variables: bool = kwargs["collect_variables"] if "collect_variables" in kwargs else True
        self.term_relaxer = TermRelaxer()
        self.constraint_counter: int = 1
        self.unwanted = ["ASTType.BooleanConstant", "ASTType.BodyAggregate", "ASTType.TheoryAtom", "ASTType.Aggregate"]


    def visit_Statement(self, stm: AST) -> AST:
        """
            Visit a statement. If it is an integrity constraint, give it a new head literal.
        """
        if is_constraint(stm):
            stm.head = self._make_head_literal(stm)
        return stm

    def _make_head_literal(self, rule: AST) -> AST:
        """ Returns a new head literal for a rule.
        """
        # Collect variables from body if collect_variables 
        variables = self._get_variables(rule) if self.collect_variables else None

        location = rule.head.location
        args = [SymbolicTerm(location, ClingoFunction(f'r{self._constraint_number()}', [], True))]
        if variables:
            args.append(Function(location, '', variables,0))
        
        return Literal(location = location,
                    sign = 0,
                    atom = SymbolicAtom(Function(location, self.head_name, args, 0)))

    def _constraint_number(self) -> int:
        """
            Return the current integrity constraint's number and increase the count.
        """
        i = self.constraint_counter
        self.constraint_counter += 1
        return i

    def _get_variables(self, rule: AST) -> List[AST]:
        collector = []
        # iterate over body elements
        for b in rule.body:
            # if b is a literal, 
            if str(b.ast_type) == "ASTType.Literal":
                atom_type = str(b.atom.ast_type)
                # if b.atom is not BooleanConstant, BodyAggregate, TheoryAtom, Aggregate
                # and b is positive: visit it
                if atom_type not in self.unwanted and b.sign == Sign.NoSign:
                    self.term_relaxer.visit(b.atom, adder=self.add_to_collector(collector))
        # return collected variables. Keep order but remove duplicates
        return sorted(set(collector), key=lambda x: collector.index(x))

    def add_to_collector(self, collector: List[AST]) -> callable:
        def adder(Variable: AST) -> None:
            collector.append(Variable)
        return adder
    

def relax_constraints(relaxer: ProgramRelaxer, program: str) -> AST:
    """
        Relax constraints in a program and add minimization statement.
        Returns the relaxed program as an AST.

        :param relaxer: An instance of the relaxer class.
        :param program: The program to relax.
    """
    # Add minimization statement
    program += f"\n:~ {relaxer.head_name}(R,T).[1,R,T]" if \
                    relaxer.collect_variables else f"\n:~ {relaxer.head_name}(R).[1,R]"
    relaxed_program = []
    parse_string(program, lambda stm: relaxed_program.append(relaxer.visit_Statement(stm)))
    return relaxed_program