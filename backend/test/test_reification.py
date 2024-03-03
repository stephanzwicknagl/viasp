from typing import List

from clingo.ast import AST, ASTType, parse_string

from viasp.asp.reify import ProgramAnalyzer, transform


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
    assertProgramEqual(
        transform(program,
                  h=analyzer.get_conflict_free_h(),
                  model=analyzer.get_conflict_free_model()),
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
    h(1, a(X), (f(X),b(X))) :- a(X), b(X), X=1..3, f(X)."""
    assertProgramEqual(transform(rule), parse_program_to_ast(expected))


def test_head_aggregate_groups_is_transformed_correctly():
    rule = "{a(X) : b(X), c(X); d(X) : e(X), X=1..3 }:- f(X)."
    expected = """#program base.
    h(1, d(X), (f(X),e(X))) :- d(X), e(X), X=1..3, f(X).
    h(1, a(X), (f(X),c(X),b(X))) :- a(X), b(X), c(X), f(X)."""
    assertProgramEqual(transform(rule), parse_program_to_ast(expected))


def test_aggregate_choice_is_transformed_correctly():
    rule = "1{a(X) : b(X), c(X); d(X) : e(X), X=1..3 }1:- f(X)."
    expected = """#program base.
    h(1, d(X), (f(X),e(X))) :- d(X), e(X), X=1..3, f(X).
    h(1, a(X), (f(X),c(X),b(X))) :- a(X), b(X), c(X), f(X)."""
    assertProgramEqual(transform(rule), parse_program_to_ast(expected))


def test_multiple_conditional_groups_in_head():
    rule = "1 #sum { X,Y : a(X,Y) : b(Y), c(X) ; X,Z : b(X,Z) : e(Z) }  :- c(X)."
    expected = """#program base.
    h(1, a(X,Y), (c(X),b(Y))) :- a(X,Y), b(Y), c(X). 
    h(1, b(X,Z), (c(X), e(Z))) :- b(X,Z), e(Z), c(X). 
    """
    assertProgramEqual(transform(rule), parse_program_to_ast(expected))


def test_multiple_aggregates_in_body():
    rule = "s(Y) :- r(Y), 2 #sum{X : p(X,Y), q(X) } 7."
    expected = "#program base. h(1, s(Y), (r(Y),)) :- s(Y), r(Y), 2 #sum{X : p(X,Y), q(X) } 7."
    assertProgramEqual(transform(rule), parse_program_to_ast(expected))

def test_aggregates_in_body():
    rule = "reached(V) :- reached(U), hc(U,V),1{edge(U,V)}."
    expected = "#program base. h(1,reached(V),(hc(U,V),reached(U))) :- reached(V); reached(U); hc(U,V); 1 <= { edge(U,V) }."
    assertProgramEqual(transform(rule), parse_program_to_ast(expected))

def test_aggregate_in_body_2():
    rule = "a(X) :- b(X), c(X),1 = {d(X) : e(X), X=1..3 }."
    expected = """#program base.
    h(1, a(X), (c(X),b(X))) :- a(X), b(X), c(X), 1 = {d(X) : e(X), X=1..3 }."""
    assertProgramEqual(transform(rule), parse_program_to_ast(expected))

def test_conditional_in_body():
    rule = "a(X) :- b(X), c(X), d(X) : e(X), X=1..3."
    expected = """#program base.
    h(1, a(X), (c(X),b(X))) :- a(X), b(X), c(X), d(X) : e(X), X=1..3."""
    assertProgramEqual(transform(rule), parse_program_to_ast(expected))

def test_comparison_in_body():
    rule = "a(X) :- b(X), X < 2."
    expected = """#program base.
    h(1, a(X), (b(X),)) :- a(X), b(X), X < 2."""
    assertProgramEqual(transform(rule), parse_program_to_ast(expected))

def test_boolean_constant_in_body():
    rule = "a(X) :- b(X), c(X), #true."
    expected = """#program base.
    h(1, a(X), (c(X),b(X))) :- a(X), b(X), c(X), #true."""
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

def test_showTerm_transformed_correctly():
    rule = "#show a : b."
    expected = "h_showTerm(1, a, (b,)) :- showTerm(a), b."
    assertProgramEqual(transform(rule), parse_program_to_ast(expected))

    rule = "#show a(X) : b(X)."
    expected = "h_showTerm(1, a(X), (b(X),)) :- showTerm(a(X)), b(X)."
    assertProgramEqual(transform(rule), parse_program_to_ast(expected))
