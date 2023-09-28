from clingo.ast import Transformer as ClingoTransformer, AST
from clingo import ast, Number, SymbolType
from typing import List, Union, Tuple, Any
import os

transformer_path = str(os.path.abspath(__file__))
class Transformer(ClingoTransformer):
    transformer_path: str 

    def __init__(self):
        self.conflict_free_x: int = 1
        self.max = Number(30)

    def binary_operation(self, location: AST, operator: str, left: AST, right: AST) -> AST:
        operator_number = 4
        if operator == "^":
            operator_number = 0
        elif operator == "?":
            operator_number = 1
        elif operator == "&":
            operator_number = 2
        elif operator == "+":
            operator_number = 3
        elif operator == "-":
            operator_number = 4
        elif operator == "*":
            operator_number = 5
        elif operator == "/":
            operator_number = 6
        elif operator == "\\":
            operator_number = 7
        elif operator == "**":
            operator_number = 8

        return ast.BinaryOperation(
            location, operator_number, left, right)

    def make_dl_literals(self, location: AST, term: AST) -> Tuple[Union[str, AST], AST]:
        if getattr(term, "ast_type", List) == ast.ASTType.SymbolicTerm and \
                getattr(getattr(term, "symbol", None), "type", None) == SymbolType.Number:
            return (term.symbol, term)
        else:
            conflict_free_x = '_'*self.conflict_free_x+'X'
            self.conflict_free_x += 1

            inner_var = ast.Function(
                location, '', term, 0) if isinstance(term, list) else term
            inner_X = ast.Variable(location, conflict_free_x)
            outer_function = ast.Function(
                location, 'dl', [inner_var, inner_X], 0)
            outer_symatom = ast.SymbolicAtom(outer_function)
            return (conflict_free_x, ast.Literal(location, 0, outer_symatom))

    def visit_TheoryAtom(self, atom: AST, **kwargs: Any) -> Tuple[AST, AST, List[str]]:
        term = atom.term
        guard: List[AST] = []
        sequence_operations: List = []
        dl_literals = []
        if term.name == "diff":
            content: List[Union[AST, List[AST]]] = []
            self.visit_children(atom, theory_content=content,  collect_guard=guard,
                                collect_operations=sequence_operations, **kwargs)
            for i in content:
                dl_literals.append(self.make_dl_literals(term.location, i))
        return dl_literals, guard, sequence_operations

    def visit_TheoryAtomElement(self, atom_element: AST, **kwargs: Any) -> AST:
        kwargs.update({"in_elem": True})
        return atom_element.update(**self.visit_children(atom_element, **kwargs))

    def visit_TheoryGuard(self, guard: AST, **kwargs: Any) -> AST:
        collect_guard = kwargs.get("collect_guard", [])
        # Guard: 0=">", 1="<", 2="<=", 3=">=", 4="!=", 5="=", 6=no operator
        operation_number = 5
        if guard.operator_name == ">":
            operation_number = 0
        elif guard.operator_name == "<":
            operation_number = 1
        elif guard.operator_name == "<=":
            operation_number = 2
        elif guard.operator_name == ">=":
            operation_number = 3
        elif guard.operator_name == "!=":
            operation_number = 4
        elif guard.operator_name == "=":
            operation_number = 5
        guard_term = self.visit(guard.term, **kwargs)

        guard = ast.Guard(operation_number, guard_term)
        collect_guard.append(guard)

        return guard

    def visit_SymbolicTerm(self, term: AST, **kwargs: Any) -> AST:
        in_elem = kwargs.get("in_elem", False)
        if in_elem:
            kwargs.get("theory_content", []).append(term)
        return term

    def visit_Variable(self, variable: AST, **kwargs: Any) -> AST:
        in_elem = kwargs.get("in_elem", False)
        if in_elem:
            kwargs.get("theory_content", []).append(variable)
        return variable

    def visit_TheorySequence(self, sequence: AST, **kwargs: Any) -> AST:
        in_elem = kwargs.get("in_elem", False)
        theory_content = kwargs.get("theory_content", [])
        if in_elem:
            variables: List[AST] = []
            for s in sequence.terms:
                variables.append(s)
            theory_content.append(variables)
        return sequence

    def visit_TheoryFunction(self, term: AST, **kwargs: Any) -> AST:
        in_elem = kwargs.get("in_elem", False)
        theory_content = kwargs.get("theory_content", [])
        if in_elem:
            theory_content.append(term)
        return term

    def visit_TheoryUnparsedTerm(self, term: AST, **kwargs: Any) -> AST:
        in_elem = kwargs.get("in_elem", False)
        if in_elem:
            # collect content in TheorySequence
            return term.update(**self.visit_children(term, **kwargs))
        else:
            # collect and parse the guard into a Guard
            guard_term: AST = None
            for e in term.elements:
                guard_term = self.visit(e, **kwargs)
            return guard_term

    def visit_TheoryUnparsedTermElement(self, element: AST, **kwargs: Any) -> AST:
        in_elem = kwargs.get("in_elem", False)
        collect_operations = kwargs.get("collect_operations", [])
        guard_term = kwargs.get("guard_term", None)
        if in_elem:
            collect_operations.extend(element.operators)
            return element.update(**self.visit_children(element, **kwargs))
        else:
            loc = element.term.location
            operator = element.operators[0]

            if guard_term == None:
                # unary operator: 0 = -, 1 = ~, 2 = absolute value, 3 = no operator
                operator_number = 3
                if operator == "-":
                    operator_number = 0
                elif operator == "~":
                    operator_number = 1
                elif operator == "|":
                    operator_number = 2
                return ast.UnaryOperation(loc, operator_number, element.term)
            else:
                return self.binary_operation(loc, operator, guard_term, element.term)

    def visit_Rule(self, rule: AST, **kwargs: Any) -> Union[AST, List[AST]]:
        """
        Transform ``diff`` in rule for clingo-dl

        % input rule
            &diff(head) { (T,M)-(T,M+1) } <= -D :- duration(T,M,D).
            
        % resulting rules
            { dl((T,M),X) : X=0..max ; dl((T,M+1),X):X=0..max} :- duration(T,M,D).
            :- not { dl((T,M),X) : X=0..max }  = 1, duration(T,M,D).
            :- not {dl((T,M+1),X) : X=0..max } = 1, duration(T,M,D).
            :- dl((T,M),_X), dl((T,M+1),__X), not _X-__X<=-D, duration(T,M,D).
        """
        # transform only if head is TheoryAtom
        if rule.head.ast_type == ast.ASTType.TheoryAtom:
            # initialize variables
            new_rules: List[AST] = []
            loc = rule.location

            # list of literals, e.g. [dl((T,M),X)]
            dl_literals, theory_guard, operators = self.visit(rule.head)
            conditionals = self.make_conditional_literals(loc, dl_literals)

            # make the choice rule
            new_rules.append(
                ast.Rule(loc,
                         ast.Aggregate(loc,
                                       None,
                                       conditionals,
                                       None),
                         rule.body))

            # make the individual integrity constraints
            for conditional_literal in conditionals:
                guard = ast.Guard(5, ast.SymbolicTerm(loc, Number(1)))
                aggregate = ast.Aggregate(
                    loc, guard, [conditional_literal], None)
                new_body = [ast.Literal(loc, 1, aggregate)]
                new_body.extend(rule.body)
                new_rules.append(
                    ast.Rule(loc,
                             ast.Literal(loc, 0, ast.BooleanConstant(0)),
                             new_body))

            # make the combined integrity constrain
            # from theory_guard make the guard for the combined integrity constraint
            combined_integrity_body: List[AST] = []
            dl_variables: List[AST] = []
            comparison_term: AST = None
            for variable, dl_lit in dl_literals:
                if dl_lit.ast_type == ast.ASTType.Literal:
                    combined_integrity_body.append(dl_lit)
                    dl_variables.append(ast.Variable(loc, variable))
                else:
                    dl_variables.append(dl_lit)
            for i_op, op in enumerate(operators):
                if comparison_term == None:
                    comparison_term = self.binary_operation(
                        loc, op, *dl_variables[i_op:i_op+2])
                else:
                    comparison_term = self.binary_operation(
                        loc, op, comparison_term, dl_variables[i_op+1])
            comparison = ast.Comparison(comparison_term, theory_guard)
            literal = ast.Literal(loc, 1, comparison)
            combined_integrity_body.append(literal)
            combined_integrity_body.extend(rule.body)

            new_rules.append(
                ast.Rule(loc,
                         ast.Literal(loc, 0, ast.BooleanConstant(0)),
                         combined_integrity_body))

            return new_rules
        else:
            return [rule]

    def make_conditional_literals(self, location: AST, dl_literals: List[Tuple[str, AST]]) -> List[AST]:
        conditional_literals = []
        for variable, dl_lit in dl_literals:
            if dl_lit.ast_type == ast.ASTType.Literal:
                condition = [ast.Literal(location,
                                         0,
                                         ast.Comparison(
                                             ast.Variable(location, variable),
                                             [ast.Guard(5,
                                                        ast.Interval(location,
                                                                     ast.SymbolicTerm(location,
                                                                                      Number(0)),
                                                                     ast.SymbolicTerm(location,
                                                                                      self.max)))]))]
                conditional_literals.append(
                    ast.ConditionalLiteral(location, dl_lit, condition))
        return conditional_literals
