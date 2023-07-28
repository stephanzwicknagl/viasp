from typing import List

import clingo
import pytest
from clingo.ast import ASTType, parse_string

from viasp.asp.ast_types import (SUPPORTED_TYPES, UNSUPPORTED_TYPES,
                                 make_unknown_AST_enum_types)
from viasp.asp.reify import ProgramAnalyzer, transform


def assertProgramEqual(actual, expected, message=None):
    if isinstance(actual, list):
        actual = set([str(e) for e in actual])

    if isinstance(expected, list):
        expected = set([str(e) for e in expected])
    assert actual == expected, message if message is not None else f"{expected} should be equal to {actual}"


def parse_program_to_ast(prg: str) -> List[clingo.ast.AST]:
    parsed = []
    parse_string(prg, lambda rule: parsed.append(rule))
    return parsed


def test_simple_fact_is_transform_correctly():
    rule = "a."
    expected = "a."
    assertProgramEqual(transform(rule), parse_program_to_ast(expected))


def test_fact_with_variable_is_transform_correctly():
    rule = "a(1)."
    expected = "a(1)."
    assertProgramEqual(transform(rule), parse_program_to_ast(expected))


def test_normal_rule_without_negation_is_transformed_correctly():
    rule = "b(X) :- c(X)."
    expected = "h(1, b(X), (c(X),)) :- b(X), c(X)."
    assertProgramEqual(transform(rule), parse_program_to_ast(expected))


def test_multiple_nested_variable_gets_transformed_correctly():
    program = "x(1). y(1). l(x(X),y(Y)) :- x(X), y(Y)."
    expected = "x(1). y(1). h(1, l(x(X),y(Y)), (y(Y),x(X))) :- l(x(X),y(Y)), x(X), y(Y)."
    assertProgramEqual(transform(program), parse_program_to_ast(expected))


def test_conflict_variables_are_resolved():
    program = "h(42, 11). model(X) :- y(X). h_(1,2)."
    expected = "h(42, 11). h_(1,2). h__(1,model(X),(y(X),)) :- model(X), y(X)."
    analyzer = ProgramAnalyzer()
    analyzer.add_program(program)
    assertProgramEqual(transform(program, h=analyzer.get_conflict_free_h(), model=analyzer.get_conflict_free_model()),
                       parse_program_to_ast(expected))


def test_normal_rule_with_negation_is_transformed_correctly():
    rule = "b(X) :- c(X), not a(X)."
    expected = "h(1, b(X), (c(X),)) :- b(X), c(X); not a(X)."
    assertProgramEqual(transform(rule), parse_program_to_ast(expected))


def test_multiple_rules_with_same_head_do_not_lead_to_duplicate_h_with_wildcard():
    rule = "b(X) :- c(X), not a(X). b(X) :- a(X), not c(X)."
    expected = "h(1, b(X),(c(X),)) :- b(X), c(X), not a(X).h(1, b(X), (a(X),)) :- b(X), a(X), not c(X)."
    assertProgramEqual(transform(rule), parse_program_to_ast(expected))


def extract_rule_nrs_from_parsed_program(prg):
    rule_nrs = []
    for rule in prg:
        if rule.ast_type != ASTType.Rule:
            continue
        head = rule.head.atom.symbol
        if head.name == "h" and str(head.arguments[0]) != "_":
            rule_nrs.append(head.arguments[0].symbol.number)

    return rule_nrs


def test_programs_with_facts_result_in_matching_program_mappings():
    program = "b(X) :- c(X), not a(X). b(X) :- a(X), not c(X)."
    expected = "h(1, b(X), (c(X),)) :- b(X), c(X), not a(X).h(1, b(X),(a(X),)) :- b(X), a(X), not c(X)."
    parsed = parse_program_to_ast(expected)
    transformed = transform(program)
    assertProgramEqual(transformed, parsed)


def test_choice_rule_is_transformed_correctly():
    rule = "{b(X)}."
    expected = "h(1, b(X),()) :- b(X)."
    assertProgramEqual(transform(rule), parse_program_to_ast(expected))


def test_normal_rule_with_choice_in_head_is_transformed_correctly():
    rule = "{b(X)} :- c(X)."
    expected = "#program base.h(1, b(X), (c(X),)) :- b(X), c(X)."
    assertProgramEqual(transform(rule), parse_program_to_ast(expected))


def test_head_aggregate_is_transformed_correctly():
    rule = "{a(X) : b(X)}."
    expected = """#program base.
    h(1, a(X), (b(X),)) :- a(X), b(X)."""
    assertProgramEqual(transform(rule), parse_program_to_ast(expected))


def test_conditional_with_interval_transformed_correctly():
    rule = "{a(X) : b(X), X=1..3 }:- f(X)."
    expected = """#program base.
    h(1, a(X), (b(X),f(X))) :- a(X), f(X), b(X), X=1..3."""
    assertProgramEqual(transform(rule), parse_program_to_ast(expected))


def test_head_aggregate_groups_is_transformed_correctly():
    rule = "{a(X) : b(X), c(X); d(X) : e(X), X=1..3 }:- f(X)."
    expected = """#program base.
    h(1, d(X), (e(X),f(X))) :- d(X), f(X), e(X), X=1..3.
    h(1, a(X), (c(X),b(X),f(X))) :- a(X), f(X), b(X), c(X)."""
    assertProgramEqual(transform(rule), parse_program_to_ast(expected))


def test_aggregate_choice_is_transformed_correctly():
    rule = "1{a(X) : b(X), c(X); d(X) : e(X), X=1..3 }1:- f(X)."
    expected = """#program base.
    h(1, d(X), (e(X),f(X))) :- d(X), f(X), e(X), X=1..3.
    h(1, a(X), (c(X),b(X),f(X))) :- a(X), f(X), b(X), c(X)."""
    assertProgramEqual(transform(rule), parse_program_to_ast(expected))


def test_multiple_conditional_groups_in_head():
    rule = "1 #sum { X,Y : a(X,Y) : b(Y), c(X) ; X,Z : b(X,Z) : e(Z) }  :- c(X)."
    expected = """#program base.
    h(1, a(X,Y), (c(X),b(Y))) :- a(X,Y), c(X), b(Y). 
    h(1, b(X,Z), (e(Z), c(X))) :- b(X,Z), c(X), e(Z). 
    """
    assertProgramEqual(transform(rule), parse_program_to_ast(expected))


def test_multiple_aggregates_in_body():
    rule = "s(Y) :- r(Y), 2 #sum{X : p(X,Y), q(X) } 7."
    expected = "#program base. h(1, s(Y), (q(X),p(X,Y),r(Y))) :- s(Y), r(Y),  p(X,Y), q(X), 2 #sum{_X : p(_X,_Y), q(_X) } 7."
    assertProgramEqual(transform(rule), parse_program_to_ast(expected))

def test_aggregates_in_body():
    rule = "reached(V) :- reached(U), hc(U,V),1{edge(U,V)}."
    expected = "#program base. h(1,reached(V),(edge(U,V),hc(U,V),reached(U))) :- reached(V); reached(U); hc(U,V); edge(U,V); 1 <= { edge(_U,_V) }; 1 <= { edge(_U,_V) }."
    assertProgramEqual(transform(rule), parse_program_to_ast(expected))


def test_disjunctions_in_head():
    rule = "p(X); q(X) :- r(X)."
    # TODO: Below breaks this. Javier will tell you how to fix it
    # a.
    # p(1);
    # q(1).
    # p(1): - a.
    # q(1): - a.
    # Stable
    # models:
    # a, p(1) | a, q(1)
    expected = """#program base. 
    h(1, p(X), (r(X),)) :- p(X), r(X). 
    h(1, q(X), (r(X),)) :- q(X), r(X). """
    assertProgramEqual(transform(rule), parse_program_to_ast(expected))


def test_dependency_graph_creation():
    program = "a. b :- a. c :- a."

    analyzer = ProgramAnalyzer()
    result = analyzer.sort_program(program)
    assert len(result) == 2, "Facts should not be in the sorted program."
    assert len(analyzer.dependants) == 2, "Facts should not be in the dependency graph."


def test_negative_recursion_gets_grouped():
    program = "a. b :- not c, a. c :- not b, a."

    analyzer = ProgramAnalyzer()
    result = analyzer.sort_program(program)
    assert len(result) == 1, "Negative recursions should be grouped into one transformation."


def multiple_non_recursive_rules_with_same_head_should_not_be_grouped():
    program = "f(B) :- x(B). f(B) :- f(A), rel(A,B)."

    analyzer = ProgramAnalyzer()
    result = analyzer.sort_program(program)
    assert len(result) == 2, "Multiple rules with same head that are not recursive should not be grouped."


def test_sorting_facts_independent():
    program = "c :- b. b :- a. a. "
    transformer = ProgramAnalyzer()
    result = transformer.sort_program(program)
    assert len(result) == 2, "Facts should not be sorted."
    assert str(next(iter(result[0].rules))) == "b :- a."
    assert str(next(iter(result[1].rules))) == "c :- b."


def test_sorting_behemoth():
    program = "c(1). e(1). f(X,Y) :- b(X,Y). 1 #sum { X,Y : a(X,Y) : b(Y), c(X) ; X,Z : b(X,Z) : e(Z) } :- c(X). e(X) :- c(X)."
    transformer = ProgramAnalyzer()
    result = transformer.sort_program(program)
    assert len(result) == 3
    assert str(next(iter(result[0].rules))) == "e(X) :- c(X)."
    assert str(next(iter(result[1].rules))) == "1 <= #sum { X,Y: a(X,Y): b(Y), c(X); X,Z: b(X,Z): e(Z) } :- c(X)."
    assert str(next(iter(result[2].rules))) == "f(X,Y) :- b(X,Y)."


def test_data_type_is_correct():
    program = "d :- c. b :- a. a. c :- b."
    transformer = ProgramAnalyzer()
    result = transformer.sort_program(program)
    assert len(result) > 0 and len(
        result[0].rules) > 0, "Transformation should return something and the transformation should contain a rule."
    a_rule = next(iter(result[0].rules))
    data_type = type(a_rule)
    assert data_type == clingo.ast.AST, f"{a_rule} should be an ASTType, not {data_type}"


def get_reasons(prg, model):
    ctl = clingo.Control()
    ctl.add("base", [], prg)
    ctl.add("base", [], "".join(model))
    ctl.ground([("base", [])])
    reasons = []
    for x in ctl.symbolic_atoms.by_signature("h", 2):
        reasons.append(x.symbol)
    return set(reasons)


def test_aggregate_in_body_of_constraint():
    program = ":- 3 { assignedB(P,R) : paper(P) }, reviewer(R)."
    transformer = ProgramAnalyzer()
    result = transformer.sort_program(program)
    assert len(result) == 1


def test_minimized_causes_a_warning():
    program = "#minimize { 1,P,R : assignedB(P,R), paper(P), reviewer(R) }."

    transformer = ProgramAnalyzer()
    transformer.sort_program(program)
    assert len(transformer.get_filtered())


def test_disjunction_causes_error_and_doesnt_get_passed():
    program = "a; b."

    transformer = ProgramAnalyzer()
    program = transformer.sort_program(program)
    assert len(transformer.get_filtered())
    assert not len(program)


def test_minimized_is_collected_as_pass_through():
    program = "#minimize { 1,P,R : assignedB(P,R), paper(P), reviewer(R) }."

    transformer = ProgramAnalyzer()
    result = transformer.sort_program(program)
    assert not len(result)
    assert len(transformer.pass_through)


def test_ast_types_do_not_intersect():
    assert not SUPPORTED_TYPES.intersection(UNSUPPORTED_TYPES), "No type should be supported and unsupported"
    known = SUPPORTED_TYPES.union(UNSUPPORTED_TYPES)
    unknown = make_unknown_AST_enum_types()
    assert not unknown.intersection(known), "No type should be known and unknown"


@pytest.mark.skip(reason="Not implemented yet")
def test_constraints_gets_put_last():
    program = """
    { assigned(P,R) : reviewer(R) } 3 :-  paper(P).
     :- assigned(P,R), coi(R,P).
     :- assigned(P,R), not classA(R,P), not classB(R,P).
    assignedB(P,R) :-  classB(R,P), assigned(P,R).
     :- 3 { assignedB(P,R) : paper(P) }, reviewer(R).
    #minimize { 1,P,R : assignedB(P,R), paper(P), reviewer(R) }.
    """
    transformer = ProgramAnalyzer()
    result = transformer.sort_program(program)
    assert len(result) == 3
    assert len(result[0].rules) == 1
    assert len(result[1].rules) == 1
    assert len(result[2].rules) == 3
