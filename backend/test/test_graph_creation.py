from typing import List

import networkx as nx
# from clingo import Function
from clingo.ast import AST, Function, Location, Position

from viasp.asp.justify import build_graph, make_reason_path_from_facts_to_stable_model, \
    get_h_symbols_from_model
from viasp.shared.util import pairwise
from viasp.asp.reify import transform, ProgramAnalyzer, reify_list
from viasp.shared.model import Node, Transformation, SymbolIdentifier
from viasp.shared.util import get_start_node_from_graph, get_end_node_from_path
from clingo.ast import parse_string


from helper import get_stable_models_for_program


def sort_program_and_get_graph(program: str):
    analyzer = ProgramAnalyzer()
    sorted_program = analyzer.sort_program(program)
    saved_models = get_stable_models_for_program(program)
    reified = reify_list(sorted_program)

    g = build_graph(saved_models, reified, analyzer, set())
    return g


def test_justification_creates_a_graph_with_a_single_path():
    orig_program = "c(1). c(2). b(X) :- c(X). a(X) :- b(X)."
    g = sort_program_and_get_graph(orig_program)
    assert len(g.nodes()) == 3
    assert len(g.edges()) == 2


def test_justification_creates_a_graph_with_three_paths_on_choice_rules():
    orig_program = "a(1). a(2). { b(X) } :- a(X)."
    g = sort_program_and_get_graph(orig_program)
    assert len(g.nodes()) == 5
    assert len(g.edges()) == 4


def test_pairwise_works():
    lst = [0, 1, 2, 3]
    assert list(pairwise(lst)) == [(0, 1), (1, 2), (2, 3)]


def test_graph_merges_facts_together():
    orig_program = "c(1). c(2). a."
    analyzer = ProgramAnalyzer()
    sorted_program = analyzer.sort_program(orig_program)
    saved_models = get_stable_models_for_program(orig_program)
    reified = reify_list(sorted_program)

    g = build_graph(saved_models, reified, analyzer, set())
    assert len(g.nodes()) == 1
    assert len(g.edges()) == 0


def test_facts_get_merged_in_one_node():
    orig_program = "c(1). c(2). a. z(1) :- a. x(X) :- c(X)."
    analyzer = ProgramAnalyzer()
    sorted_program = analyzer.sort_program(orig_program)
    saved_models = get_stable_models_for_program(orig_program)
    reified = reify_list(sorted_program)

    g = build_graph(saved_models, reified, analyzer, set())
    assert len(g.nodes) == 3
    assert len(g.edges) == 2


def test_rules_are_transferred_to_transformations():
    orig_program = "a(1). {b(X)} :- a(X). d(X) :- b(X). {c(X)} :- b(X)."
    analyzer = ProgramAnalyzer()
    sorted_program = analyzer.sort_program(orig_program)
    saved_models = get_stable_models_for_program(orig_program)
    reified = reify_list(sorted_program)

    g = build_graph(saved_models, reified, analyzer, set())
    for _, _, t in g.edges(data=True):
        tr = t["transformation"]
        assert isinstance(tr, Transformation)
        assert tr.rules != None
        assert len(tr.rules) > 0
        assert type(next(iter(tr.rules))) == AST


def test_empty_stable_model_with_initial_choice():
    program = """{rain; sprinkler} 1.
wet :- rain.
wet :- sprinkler."""
    analyzer = ProgramAnalyzer()
    sorted_program = analyzer.sort_program(program)
    saved_models = get_stable_models_for_program(program)
    reified = reify_list(sorted_program)
    g = build_graph(saved_models, reified, analyzer, set())
    assert len(list(g.nodes)) == 10


def test_dependencies_register_on_negation():
    program = """
    {a}.
    c :- not b.
    b :- a.
    """
    analyzer = ProgramAnalyzer()
    sorted_program = analyzer.sort_program(program)
    assert len(sorted_program) == 3
    assert str(list(sorted_program[0].rules)[0]) == "{ a }."
    assert str(list(sorted_program[1].rules)[0]) == "b :- a."
    assert str(list(sorted_program[2].rules)[0]) == "c :- not b."


def test_integrity_constraints_are_preserved():
    program = """
    1 {a; b} 1.
    :- not b.
    {c} :- a, not b.
    :- c.
    """
    g = sort_program_and_get_graph(program)
    assert any(any(str(r) == "#false :- not b." for r in t["transformation"].rules) for _, _, t in g.edges(data=True))
    assert any(any(str(r) == "#false :- c." for r in t["transformation"].rules) for _, _, t in g.edges(data=True))


def test_integrity_constraints_get_sorted_last_and_merged():
    program = """
    1 {a; b} 1.
    :- not b.
    {c} :- a, not b.
    :- c.
    """
    analyzer = ProgramAnalyzer()
    sorted_program = analyzer.sort_program(program)
    assert len(sorted_program) == 3
    assert any(str(rule) == "#false :- not b." for rule in sorted_program[2].rules)
    assert any(str(rule) == "#false :- c." for rule in sorted_program[2].rules)


def test_conditional_literals():
    program = """
    p(1..3). e(1..3). b(1..3). c(1..3).
    a(4).
    { a(X) : b(X),c(X) ; d(X) : e(X),X=1..3 } =1 :- p(X).
    """
    analyzer = ProgramAnalyzer()
    sorted_program = analyzer.sort_program(program)
    saved_models = get_stable_models_for_program(program)
    reified = reify_list(sorted_program)

    g = build_graph(saved_models, reified, analyzer, set())
    assert len(g.nodes) == 9
    assert len(g.edges) == 8


def test_negative_recursion_gets_treated_correctly():
    orig_program = "a. b :- not c, a. c :- not b, a."
    analyzer = ProgramAnalyzer()
    sorted_program = analyzer.sort_program(orig_program)
    saved_models = get_stable_models_for_program(orig_program)
    reified = reify_list(sorted_program)

    g = build_graph(saved_models, reified, analyzer, set())
    assert len(g.nodes) == 3
    assert len(g.edges) == 2


def test_path_creation():
    program = "fact(1). result(X) :- fact(X). next(X) :- fact(X)."
    transformed = transform(program)
    single_saved_model = get_stable_models_for_program(program).pop()
    facts, constants = [], []
    h_symbols = get_h_symbols_from_model(single_saved_model, transformed, facts, constants)
    rule_mapping = {1: Transformation(1, parse_program_to_ast("fact(1).")), 2: Transformation(2, parse_program_to_ast("result(X) :- fact(X)."))}
    path = make_reason_path_from_facts_to_stable_model(single_saved_model,
                                                       rule_mapping, Node(frozenset(), 0),
                                                       h_symbols, set())
    nodes, edges = list(path.nodes), list(t for _, _, t in path.edges.data(True))
    assert len(edges) == 2
    assert len(nodes) == 3
    assert all([isinstance(node, Node) for node in nodes])


def test_atoms_are_propagated_correctly_through_diffs():
    program = "a. b :- a. c :- b. d :- c."
    loc = Location(Position("str",1,1), Position("str",1,1))
    transformed = transform(program)
    single_saved_model = get_stable_models_for_program(program).pop()
    facts, constants = [], []
    h_symbols = get_h_symbols_from_model(single_saved_model, transformed, facts, constants)
    rule_mapping = {1: Transformation(1, parse_program_to_ast("b :- a.")), 2: Transformation(2, parse_program_to_ast("c :- b.")), 3: Transformation(3, parse_program_to_ast("d :- c."))}
    path = make_reason_path_from_facts_to_stable_model(single_saved_model,
                                                        rule_mapping,
                                                       Node(frozenset([SymbolIdentifier(Function(loc,"a",[], False))]), 0, frozenset([Function(loc,"a", [], False)])),
                                                       h_symbols, set())
    beginning: Node = get_start_node_from_graph(path)
    end: Node = get_end_node_from_path(path)
    path_list: List[Node] = nx.shortest_path(path, beginning, end)
    for src, tgt in pairwise(path_list):
        assert src.diff.issubset(tgt.atoms)
        assert len(src.atoms) == len(tgt.atoms) - len(tgt.diff)

def parse_program_to_ast(prg: str) -> AST:
    parsed = []
    parse_string(prg, lambda rule: parsed.append(rule))
    return parsed[0]