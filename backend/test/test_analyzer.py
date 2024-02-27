import pytest
from clingo.ast import AST

from viasp.asp.ast_types import (SUPPORTED_TYPES, UNSUPPORTED_TYPES,
                                 make_unknown_AST_enum_types)
from viasp.asp.reify import ProgramAnalyzer


def test_simple_fact_analyzed_correctly(app_context):
    program = "a."
    transformer = ProgramAnalyzer()
    program = transformer.sort_program(program)
    assert transformer.get_filtered() == []
    assert transformer.will_work()


def test_fact_with_variable_analyzed_correctly(app_context):
    program = "a(1)."
    transformer = ProgramAnalyzer()
    program = transformer.sort_program(program)
    assert transformer.get_filtered() == []
    assert transformer.will_work()


def test_disjunction_causes_error_and_doesnt_get_passed(app_context):
    program = "a; b."
    transformer = ProgramAnalyzer()
    program = transformer.sort_program(program)
    assert len(transformer.get_filtered())
    assert not len(program)
    assert not transformer.will_work()


def test_simple_rule_analyzed_correctly(app_context):
    program = "a :- b."
    transformer = ProgramAnalyzer()
    program = transformer.sort_program(program)
    assert transformer.get_filtered() == []
    assert transformer.will_work()


def test_rule_without_negation_analyzed_correctly(app_context):
    program = "a :- b, c."
    transformer = ProgramAnalyzer()
    program = transformer.sort_program(program)
    assert transformer.get_filtered() == []
    assert transformer.will_work()


def test_rule_with_negation_analyzed_correctly(app_context):
    program = "a :- not b, c."
    transformer = ProgramAnalyzer()
    program = transformer.sort_program(program)
    assert transformer.get_filtered() == []
    assert transformer.will_work()


def test_multiple_nested_variable_analyzed_correctly(app_context):
    program = "x(1). y(1). l(x(X),y(Y)) :- x(X), y(Y)."
    transformer = ProgramAnalyzer()
    program = transformer.sort_program(program)
    assert transformer.get_filtered() == []
    assert transformer.will_work()


def test_show_statement_without_terms_analyzed_correctly(app_context):
    program = "#show a/1."
    transformer = ProgramAnalyzer()
    program = transformer.sort_program(program)
    assert transformer.get_filtered() == []
    assert transformer.will_work()


def test_show_statement_with_terms_analyzed_correctly(app_context):
    program = "a. #show b : a."

    transformer = ProgramAnalyzer()
    result = transformer.sort_program(program)
    assert transformer.get_filtered(
    ) == [], "Show Term should not be filtered out."
    assert transformer.will_work(), "Program with ShowTerm should work."
    assert str(next(iter(result[0].rules))) == "#show b : a."


def test_defined_statement_analyzed_correctly(app_context):
    program = "#defined a/1."
    expected = "#defined a/1."
    transformer = ProgramAnalyzer()
    program = transformer.sort_program(program)
    filtered = transformer.get_filtered()
    will_work = transformer.will_work()
    assert filtered == [], "Defined Statement should not be filtered out."
    assert will_work == True, "Program with DefinedTerm should work."
    # assertProgramEqual(rules, parse_program_to_ast(expected))


def test_definition_statement_analyzed_correctly(app_context):
    program = "#const max=1."
    transformer = ProgramAnalyzer()
    program = transformer.sort_program(program)
    filtered = transformer.get_filtered()
    will_work = transformer.will_work()
    assert filtered == [], "Definition Statement should not be filtered out."
    assert will_work == True, "Program with DefinitionTerm should work."
    # assertProgramEqual(rules, parse_program_to_ast(expected))'


def test_script_statement_analyzed_correctly(app_context):
    program = """
#script(python)
from clingo.symbol import Number
def test2():
    return Number(42)
#end.
1{a;b;p(@test2())}.
"""
    transformer = ProgramAnalyzer()
    program = transformer.sort_program(program)
    filtered = transformer.get_filtered()
    will_work = transformer.will_work()
    assert len(filtered) == 1, "Script Statement should be filtered out."
    assert will_work == True, "Program with ScriptTerm should work."
    # assertProgramEqual(rules, parse_program_to_ast(expected))


def test_program_statement_analyzed_correctly(app_context):
    program = "#program base."
    expected = "#program base."
    transformer = ProgramAnalyzer()
    program = transformer.sort_program(program)
    filtered = transformer.get_filtered()
    will_work = transformer.will_work()
    assert filtered == [], "Program Statement should not be filtered out."
    assert will_work == True, "Program with ProgramTerm should work."
    # assertProgramEqual(rules, parse_program_to_ast(expected))


def test_external_statement_analyzed_correctly(app_context):
    program = "#external a(X)."
    transformer = ProgramAnalyzer()
    program = transformer.sort_program(program)
    filtered = transformer.get_filtered()
    will_work = transformer.will_work()
    assert filtered == [], "External Statement should not be filtered out."
    assert will_work == True, "Program with ExternalTerm should work."
    # assertProgramEqual(rules, parse_program_to_ast(expected))


def test_edge_statement_analyzed_correctly(app_context):
    program = "c.#edge (a, b) : c."
    transformer = ProgramAnalyzer()
    program = transformer.sort_program(program)
    filtered = transformer.get_filtered()
    will_work = transformer.will_work()
    assert len(filtered) == 1, "Edge Statement should be filtered out."
    assert will_work == True, "Program with EdgeTerm should work."


def test_heuristic_statement_analyzed_correctly(app_context):
    program = "#heuristic a : b, c. [x@y,z]"
    transformer = ProgramAnalyzer()
    program = transformer.sort_program(program)
    filtered = transformer.get_filtered()
    will_work = transformer.will_work()
    assert len(
        filtered) == 1, "Heuristic Statement should not be filtered out."
    assert will_work == True, "Program with HeuristicTerm should work."


def test_project_atom_statement_analyzed_correctly(app_context):
    program = "#project a : b, c."
    expected = "#project a : b, c."
    transformer = ProgramAnalyzer()
    program = transformer.sort_program(program)
    filtered = transformer.get_filtered()
    will_work = transformer.will_work()
    assert filtered == [], "Project Statement should not be filtered out."
    assert will_work == True, "Program with ProjectTerm should work."


def test_project_signature_statement_analyzed_correctly(app_context):
    program = "#project a/1."
    expected = "#project a/1."
    transformer = ProgramAnalyzer()
    program = transformer.sort_program(program)
    filtered = transformer.get_filtered()
    will_work = transformer.will_work()
    assert filtered == [], "Project Statement should not be filtered out."
    assert will_work == True, "Program with ProjectTerm should work."


def test_theory_definition_statement_analyzed_correctly(app_context):
    program = """
    #theory x {
    a {
        + : 1, unary;
        * : 2, binary, left;
        ^ : 3, binary, right
    };
    &b/0 : a, any;
    &c/0 : a, {+,-}, a, directive
    }.
    &b { f(a) : q } <= a * -b * c.
    """
    transformer = ProgramAnalyzer()
    program = transformer.sort_program(program)
    filtered = transformer.get_filtered()
    will_work = transformer.will_work()
    assert len(
        filtered
    ) == 16, "Theory Definition Statement should not be filtered out."
    assert will_work == True, "Program with TheoryDefinitionTerm should work."


def test_dependency_graph_creation(app_context):
    program = "a. b :- a. c :- a."

    analyzer = ProgramAnalyzer()
    result = analyzer.sort_program(program)
    assert len(result) == 2, "Facts should not be in the sorted program."
    assert len(analyzer.dependants
               ) == 2, "Facts should not be in the dependency graph."


def test_negative_recursion_gets_grouped(get_sort_program):
    program = "a. b :- not c, a. c :- not b, a."

    result, _ = get_sort_program(program)
    assert len(
        result
    ) == 1, "Negative recursions should be grouped into one transformation."


def multiple_non_recursive_rules_with_same_head_should_not_be_grouped(
        sort_program):
    program = "f(B) :- x(B). f(B) :- f(A), rel(A,B)."
    result = sort_program(program)
    assert len(
        result
    ) == 2, "Multiple rules with same head that are not recursive should not be grouped."


def test_sorting_facts_independent(get_sort_program):
    program = "c :- b. b :- a. a. "
    result, _ = get_sort_program(program)
    assert len(result) == 2, "Facts should not be sorted."
    assert str(next(iter(result[0].rules))) == "b :- a."
    assert str(next(iter(result[1].rules))) == "c :- b."


def test_sorting_behemoth(get_sort_program):
    program = "c(1). e(1). f(X,Y) :- b(X,Y). 1 #sum { X,Y : a(X,Y) : b(Y), c(X) ; X,Z : b(X,Z) : e(Z) } :- c(X). e(X) :- c(X)."
    result, _ = get_sort_program(program)
    assert len(result) == 3
    assert str(next(iter(result[0].rules))) == "e(X) :- c(X)."
    assert str(
        next(iter(result[1].rules))
    ) == "1 <= #sum { X,Y: a(X,Y): b(Y), c(X); X,Z: b(X,Z): e(Z) } :- c(X)."
    assert str(next(iter(result[2].rules))) == "f(X,Y) :- b(X,Y)."


def test_data_type_is_correct(get_sort_program):
    program = "d :- c. b :- a. a. c :- b."
    result, _ = get_sort_program(program)
    assert len(result) > 0 and len(
        result[0].rules
    ) > 0, "Transformation should return something and the transformation should contain a rule."
    a_rule = next(iter(result[0].rules))
    data_type = type(a_rule)
    assert data_type == AST, f"{a_rule} should be an ASTType, not {data_type}"


def test_aggregate_in_body_of_constraint(get_sort_program):
    program = ":- 3 { assignedB(P,R) : paper(P) }, reviewer(R)."
    result, _ = get_sort_program(program)
    assert len(result) == 1


def test_minimized_causes_no_warning(app_context):
    program = "#minimize { 1,P,R : assignedB(P,R), paper(P), reviewer(R) }."

    transformer = ProgramAnalyzer()
    transformer.sort_program(program)
    assert len(transformer.get_filtered()) == 0


def test_minimized_is_collected_as_rule(app_context):
    program = "#minimize { 1,P,R : assignedB(P,R), paper(P), reviewer(R) }."
    transformer = ProgramAnalyzer()
    result = transformer.sort_program(program)
    assert len(result)
    assert len(transformer.rules) == 1


def test_weak_minimized_is_collected_as_rule(app_context):
    program = ":~ last(N). [N@0,1]"
    transformer = ProgramAnalyzer()
    result = transformer.sort_program(program)
    assert len(result)
    assert len(transformer.rules) == 1


def test_ast_types_do_not_intersect(app_context):
    assert not SUPPORTED_TYPES.intersection(
        UNSUPPORTED_TYPES), "No type should be supported and unsupported"
    known = SUPPORTED_TYPES.union(UNSUPPORTED_TYPES)
    unknown = make_unknown_AST_enum_types()
    assert not unknown.intersection(
        known), "No type should be known and unknown"



@pytest.mark.skip(reason="Not implemented yet")
def test_constraints_gets_put_last(app_context):
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



def test_body_conditional_literal_sorted_correctly(app_context):
    program = """
    node(1..2). edge(1,2). edge(2,1).
    hc(U,V) :- edge(U,V).
    allnodes :- node(X): hc(_,X)."""
    transformer = ProgramAnalyzer()
    result = transformer.sort_program(program)
    assert len(result) == 2
    assert str(next(iter(result[0].rules))) == "hc(U,V) :- edge(U,V)."
    assert str(next(iter(result[1].rules))) == "allnodes :- node(X): hc(_,X)."

    assert len(transformer.dependants[(
        'allnodes', 0)]) == 1, "allnodes/0 should depend on one rule."
    assert len(transformer.conditions[(
        'node', 1)]) == 1, "Node/1 should be a condition of the rule"
    assert len(transformer.conditions[(
        'hc', 2)]) == 1, "hc/2 should be a condition of the rule"


def test_body_conditional_literal_sorted_correctly_2(app_context):
    program = """
    node(1..2). edge(1,2). edge(2,1).
    hc(U,V) :- edge(U,V).
    allnodes :- hc(_,X): node(X), X=1..2."""
    transformer = ProgramAnalyzer()
    result = transformer.sort_program(program)
    assert len(result) == 2
    assert str(next(iter(result[0].rules))) == "hc(U,V) :- edge(U,V)."
    assert str(next(iter(
        result[1].rules))) == "allnodes :- hc(_,X): node(X), X = (1..2)."

    assert len(transformer.dependants[(
        'allnodes', 0)]) == 1, "allnodes/0 should depend on one rule."
    assert len(transformer.conditions[(
        'node', 1)]) == 1, "Node/1 should be a condition of the rule"
    assert len(transformer.conditions[(
        'hc', 2)]) == 1, "hc/2 should be a condition of the rule"
    assert len(
        transformer.conditions[('X = (1..2)', 0)]) == 0, "Body arithmetic is filtered from conditions."


def test_body_conditional_literal_sorted_in_show_term(app_context):
    program = """
    node(1..2). edge(1,2). edge(2,1).
    hc(U,V) :- edge(U,V).
    #show allnodes : node(X): hc(_,X)."""
    transformer = ProgramAnalyzer()
    result = transformer.sort_program(program)
    assert len(result) == 2
    assert str(next(iter(result[0].rules))) == "hc(U,V) :- edge(U,V)."
    assert str(next(iter(
        result[1].rules))) == "#show allnodes : node(X): hc(_,X)."

    assert len(transformer.dependants[(
        'allnodes', 0)]) == 1, "allnodes/0 should depend on one rule."
    assert len(transformer.conditions[(
        'node', 1)]) == 1, "Node/1 should be a condition of the rule"
    assert len(transformer.conditions[(
        'hc', 2)]) == 1, "hc/2 should be a condition of the rule"


def test_body_aggregate_sorted_correctly(app_context):
    program = """
    node(1..2). edge(1,2). edge(2,1).
    hc(U,V) :- edge(U,V).
    pathExists :- 1 < #count { 1,X,Y: hc(X,Y) }."""
    transformer = ProgramAnalyzer()
    result = transformer.sort_program(program)
    assert len(result) == 2
    assert str(next(iter(result[0].rules))) == "hc(U,V) :- edge(U,V)."
    assert str(next(iter(
        result[1].rules))) == "pathExists :- 1 < #count { 1,X,Y: hc(X,Y) }."

    assert len(transformer.dependants[(
        'pathExists', 0)]) == 1, "pathExists/0 should depend on one rule."
    assert len(transformer.conditions[(
        'hc', 2)]) == 1, "hc/2 should be a condition of the rule"


def test_body_aggregate_sorted_in_show_term(app_context):
    program = """
    node(1..2). edge(1,2). edge(2,1).
    hc(U,V) :- edge(U,V).
    #show pathExists : 1 < #count { 1,X,Y: hc(X,Y) }."""
    transformer = ProgramAnalyzer()
    result = transformer.sort_program(program)
    assert len(result) == 2
    assert str(next(iter(result[0].rules))) == "hc(U,V) :- edge(U,V)."
    assert str(next(iter(result[1].rules))
               ) == "#show pathExists : 1 < #count { 1,X,Y: hc(X,Y) }."

    assert len(transformer.dependants[(
        'pathExists', 0)]) == 1, "pathExists/0 should depend on one rule."
    assert len(transformer.conditions[(
        'hc', 2)]) == 1, "hc/2 should be a condition of the rule"
