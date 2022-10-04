from typing import List
from clingo.ast import AST, Symbol, Id, Rule, SymbolicTerm, Function, Literal, SymbolicAtom

import clingo
import clingo.ast
from clingo.ast import parse_string
from .utils import is_constraint

class Relaxer:
    def visit_children(self, x, *args, **kwargs):
        with open("transform.log", "a") as f:
            f.write(f"visit_children of {x}\n")

        for key in x.child_keys:
            with open("transform.log", "a") as f:
                f.write(f"key {key}\n")
            setattr(x, key, self.visit(getattr(x, key), *args, **kwargs))
        return x

    def visit(self, x, *args, **kwargs):
        with open("transform.log", "a") as f:
            f.write(f"ast {x}\n")
        if isinstance(x, AST):
            with open("transform.log", "a") as f:
                f.write(f"ast type: {x.ast_type}\n")
            attr = 'visit_' + str(x.ast_type).replace('ASTType.', '')
            if hasattr(self, attr):
                return getattr(self, attr)(x, *args, **kwargs)
            else:
                return self.visit_children(x, *args, **kwargs)
        elif isinstance(x, list):
            return [self.visit(y, *args, **kwargs) for y in x]
        elif x is None:
            return x
        else:
            raise TypeError("unexpected type")

class TermRelaxer(Relaxer):
    def __init__(self):
        pass

    def visit_Function(self, term):
        term.arguments.append(Symbol(term.location))
        return term

    # def visit_Symbol(self, term):
    #     # this function is not necessary if gringo's parser is used
    #     # but this case could occur in a valid AST
    #     fun = term.symbol
    #     assert(fun.type == clingo.SymbolType.Function)
    #     term.symbol = clingo.Function(fun.name, fun.arguments + [self], fun.positive)
    #     return term

class ProgramRelaxer(Relaxer):
    def __init__(self, head_name="unsat", get_variables=True):
        self.head_name: str = head_name
        self.get_variables: bool = get_variables
        self.relaxed_program: List[AST] = []
        self.term_relaxer = TermRelaxer()
        self.constraint_counter: int = 1

    # def visit_SymbolicAtom(self, atom):
    #     atom.term = self.term_transformer.visit(atom.term)
    #     return atom

    def visit_Rule(self, rule):
        if is_constraint(rule):
            with open("transform.log", "a") as f:
                f.write(f"rule is a constraint: {rule} \n")
            arguments = List[AST]
            if self.get_variables:
                with open("transform.log", "a") as f:
                    f.write(f"rule body: {rule.body}\n")
                # get arguments of body:
                for term in rule.body:
                    with open("transform.log", "a") as f:
                        f.write(f"term: {term}\n")
                    arguments.append(self.term_relaxer.visit(term)) #Q which terms are relevant?
                # create new rule head:
            rule.head = self._make_head_literal(rule, arguments)
        self._register_relaxed_program(rule)

    def visit_Program(self, prg):
        # prg.parameters.append(Id(prg.location, self.parameter.name))
        return prg

    # def visit_ShowSignature(self, sig):
    #     sig.arity += 1
    #     return sig

    # def visit_ProjectSignature(self, sig):
    #     sig.arity += 1
    #     return sig
    
    def relax_constraints(self, program: str) -> str:
        with open("transform.log", "a") as f:#
            f.write(f"program: {program}\n")
        parse_string(program, lambda statement: self.visit(statement))
        stringified = "".join(map(str, self.relaxed_program))

        if self.get_variables:
            stringified += ":~ unsat(R,T).[1,R,T]"
        else:
            stringified += ":~ unsat(R).[1,R]"
        return stringified
    
    def _register_relaxed_program(self, rule: AST):
        self.relaxed_program.append(rule)

    def _make_head_literal(self, rule: Rule, inner_args: List[AST]) -> Literal:
        location = rule.head.location
        args = [SymbolicTerm(location, clingo.Function(f'r{self._constraint_number()}', [], True))]
        if inner_args != []:
            args = args + inner_args
        atom = SymbolicAtom(Function(location, self.head_name, args, 0))

        return Literal(location, 0, atom)
    
    def _constraint_number(self) -> int:
        i = self.constraint_counter
        self.constraint_counter += 1
        return i

def main(prg):
    with prg.builder() as b:
        t = ProgramRelaxer(clingo.Function("k"))
        clingo.parse_program(
            open("example.lp").read(),
            lambda stm: b.add(t.visit(stm)))
    prg.ground([("base", [clingo.Number(i)]) for i in range(3)])
    prg.solve()