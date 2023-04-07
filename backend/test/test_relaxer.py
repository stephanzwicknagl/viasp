from typing import List
from clingo.ast import parse_string, AST
from viasp.asp.relax import relax_constraints, ProgramRelaxer


def assertProgramEqual(actual, expected, message=None):
    if isinstance(actual, list):
        actual = set([str(e) for e in actual])

    if isinstance(expected, list):
        expected = set([str(e) for e in expected])
    assert actual == expected, message if message is not None else f"{expected} should be equal to {actual}"


def parse_program_to_ast(prg: str) -> List[AST]:
    parsed = []
    parse_string(prg, lambda rule: parsed.append(rule))
    return parsed


def test_minimize_statement_with_variable_collection_add_correctly():
    rule = "a."
    expected = "a.:~unsat(R,T).[1,R,T]"
    visitor = ProgramRelaxer(head_name = "unsat", collect_variables = True)
    assertProgramEqual(relax_constraints(visitor,rule), parse_program_to_ast(expected))


def test_minimize_statement_no_variable_collection_add_correctly():
    rule = "a."
    expected = "a.:~teststring(R).[1,R]"
    visitor = ProgramRelaxer(head_name = "teststring", collect_variables = False)
    assertProgramEqual(relax_constraints(visitor,rule), parse_program_to_ast(expected))


def test_head_added_no_variables_to_collect():
    rule = "a(1).:-a(1)."
    expected = "a(1).unsat(r1) :- a(1).:~ unsat(R,T). [1@0,R,T]"
    visitor = ProgramRelaxer(head_name = "unsat", collect_variables = True)
    assertProgramEqual(relax_constraints(visitor,rule), parse_program_to_ast(expected))


def test_simple_variable_collect_correctly():
    rule = "c(1..3).d(X):-c(X).:- d(X), X=1..3."
    expected = "c((1..3)).d(X) :- c(X).unsat(r1,(X,)) :- d(X); X = (1..3).:~ unsat(R,T). [1,R,T]"
    visitor = ProgramRelaxer(head_name = "unsat", collect_variables = True)
    assertProgramEqual(relax_constraints(visitor,rule), parse_program_to_ast(expected))


def test_nested_variable_collect_correctly():
    rule = "c(1..3).d(X):-c(X).:- d(X, c(Y)), X=1..3."
    expected = "c((1..3)).d(X) :- c(X).unsat(r1,(X,Y)) :- d(X, c(Y)); X = (1..3).:~ unsat(R,T). [1,R,T]"
    visitor = ProgramRelaxer(head_name = "unsat", collect_variables = True)
    assertProgramEqual(relax_constraints(visitor,rule), parse_program_to_ast(expected))

def test_multiple_variable_collect_correctly():
    rule = "c(1..3).d(X):-c(X).:- d(X), X=1..3,X<Y."
    expected = "c((1..3)).d(X) :- c(X).unsat(r1,(X,Y)) :- d(X); X = (1..3),X<Y.:~ unsat(R,T). [1,R,T]"
    visitor = ProgramRelaxer(head_name = "unsat", collect_variables = True)
    assertProgramEqual(relax_constraints(visitor,rule), parse_program_to_ast(expected))

def test_unwanted_BooleanConstant():
    rule = "c(1..3).d(X):-c(X).:- #false."
    expected = "c((1..3)).d(X) :- c(X).unsat(r1) :- #false.:~ unsat(R,T). [1,R,T]"
    visitor = ProgramRelaxer(head_name = "unsat", collect_variables = True)
    assertProgramEqual(relax_constraints(visitor,rule), parse_program_to_ast(expected))

def test_unwanted_BodyAggregate():
    rule = "c(1..3).d(X):-c(X).:- #count{X:c(X)}=Y, d(Y), 1=#sum{1,Z:c(Z)}."
    expected = "c((1..3)).d(X) :- c(X).unsat(r1,(Y,)) :- #count{X:c(X)}=Y; d(Y); 1 = #sum { 1,Z: c(Z) }.:~ unsat(R,T). [1,R,T]"
    visitor = ProgramRelaxer(head_name = "unsat", collect_variables = True)
    assertProgramEqual(relax_constraints(visitor,rule), parse_program_to_ast(expected))

def test_unwanted_TheoryAtom():
    rule = "c(1..3).d(X):-c(X).:- &diff {0-X}<Y, c(Y)."
    expected = "c((1..3)).d(X) :- c(X).unsat(r1,(Y,)) :- &diff {0-X}<Y, c(Y).:~ unsat(R,T). [1,R,T]"
    visitor = ProgramRelaxer(head_name = "unsat", collect_variables = True)
    assertProgramEqual(relax_constraints(visitor,rule), parse_program_to_ast(expected))

def test_unwanted_Conditional():
    rule = "c(1..3).d(X):-c(X).:- g(X): X=1..3."
    expected = "c((1..3)).d(X) :- c(X).unsat(r1) :- g(X): X=1..3.:~ unsat(R,T). [1,R,T]"
    visitor = ProgramRelaxer(head_name = "unsat", collect_variables = True)
    assertProgramEqual(relax_constraints(visitor,rule), parse_program_to_ast(expected))

def test_negation_literal():
    rule = "c(1..3).d(X):-c(X).:- not d(X)."
    expected = "c((1..3)).d(X) :- c(X).unsat(r1) :- not d(X).:~ unsat(R,T). [1,R,T]"
    visitor = ProgramRelaxer(head_name = "unsat", collect_variables = True)
    assertProgramEqual(relax_constraints(visitor,rule), parse_program_to_ast(expected))

def test_double_negation_literal():
    rule = "c(1..3).d(X):-c(X).:- not not d(X)."
    expected = "c((1..3)).d(X) :- c(X).unsat(r1) :- not not d(X).:~ unsat(R,T). [1,R,T]"
    visitor = ProgramRelaxer(head_name = "unsat", collect_variables = True)
    assertProgramEqual(relax_constraints(visitor,rule), parse_program_to_ast(expected))