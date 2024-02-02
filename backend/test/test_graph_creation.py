from typing import List

import networkx as nx
from clingo.ast import AST, Function, Location, Position

from viasp.asp.justify import make_reason_path_from_facts_to_stable_model, \
    get_h_symbols_from_model
from viasp.shared.util import pairwise
from viasp.asp.reify import transform
from viasp.shared.model import Node, Transformation, SymbolIdentifier
from viasp.shared.util import get_start_node_from_graph, get_end_node_from_path


from helper import get_stable_models_for_program, parse_program_to_ast


def test_justification_creates_a_graph_with_a_single_path(get_sort_program_and_get_graph):
    program = "c(1). c(2). b(X) :- c(X). a(X) :- b(X)."
    graph_info, _ = get_sort_program_and_get_graph(program)
    g = nx.node_link_graph(graph_info[0])
    assert len(g.nodes()) == 3
    assert len(g.edges()) == 2


def test_justification_creates_a_graph_with_three_paths_on_choice_rules(get_sort_program_and_get_graph):
    program = "a(1). a(2). { b(X) } :- a(X)."
    graph_info, _ = get_sort_program_and_get_graph(program)
    g = nx.node_link_graph(graph_info[0])
    assert len(g.nodes()) == 5
    assert len(g.edges()) == 4


def test_pairwise_works():
    lst = [0, 1, 2, 3]
    assert list(pairwise(lst)) == [(0, 1), (1, 2), (2, 3)]


def test_graph_merges_facts_together(get_sort_program_and_get_graph):
    program = "c(1). c(2). a."
    graph_info, _ = get_sort_program_and_get_graph(program)
    g = nx.node_link_graph(graph_info[0])
    assert len(g.nodes()) == 1
    assert len(g.edges()) == 0


def test_facts_get_merged_in_one_node(get_sort_program_and_get_graph):
    program = "c(1). c(2). a. z(1) :- a. x(X) :- c(X)."
    graph_info, _ = get_sort_program_and_get_graph(program)
    g = nx.node_link_graph(graph_info[0])
    assert len(g.nodes) == 3
    assert len(g.edges) == 2


def test_rules_are_transferred_to_transformations(get_sort_program_and_get_graph):
    program = "a(1). {b(X)} :- a(X). d(X) :- b(X). {c(X)} :- b(X)."
    graph_info, _ = get_sort_program_and_get_graph(program)
    g = nx.node_link_graph(graph_info[0])
    for _, _, t in g.edges(data=True):
        tr = t["transformation"]
        assert isinstance(tr, Transformation)
        assert tr.rules != None
        assert len(tr.rules) > 0
        assert type(next(iter(tr.rules))) == AST


def test_empty_stable_model_with_initial_choice(get_sort_program_and_get_graph):
    program = """
        {rain; sprinkler} 1.
        wet :- rain.
        wet :- sprinkler.
    """
    graph_info, _ = get_sort_program_and_get_graph(program)
    g = nx.node_link_graph(graph_info[0])
    assert len(list(g.nodes)) == 10


def test_dependencies_register_on_negation(load_analyzer):
    program = """
        {a}.
        c :- not b.
        b :- a.
    """
    analyzer = load_analyzer(program)
    sorted_program = next(analyzer.get_sorted_program())
    assert len(sorted_program) == 3
    assert str(list(sorted_program[0].rules)[0]) == "{ a }."
    assert str(list(sorted_program[1].rules)[0]) == "b :- a."
    assert str(list(sorted_program[2].rules)[0]) == "c :- not b."


def test_integrity_constraints_are_preserved(get_sort_program_and_get_graph):
    program = """
    1 {a; b} 1.
    :- not b.
    {c} :- a, not b.
    :- c.
    """
    graph_info, _ = get_sort_program_and_get_graph(program)
    g = nx.node_link_graph(graph_info[0])
    assert any(any(str(r) == "#false :- not b." for r in t["transformation"].rules) for _, _, t in g.edges(data=True))
    assert any(any(str(r) == "#false :- c." for r in t["transformation"].rules) for _, _, t in g.edges(data=True))


def test_integrity_constraints_get_sorted_last_and_merged(load_analyzer):
    program = """
    1 {a; b} 1.
    :- not b.
    {c} :- a, not b.
    :- c.
    """
    analyzer = load_analyzer(program)
    sorted_program = next(analyzer.get_sorted_program())
    assert len(sorted_program) == 3
    assert any(str(rule) == "#false :- not b." for rule in sorted_program[2].rules)
    assert any(str(rule) == "#false :- c." for rule in sorted_program[2].rules)


def test_conditional_literals(get_sort_program_and_get_graph):
    program = """
    p(1..3). e(1..3). b(1..3). c(1..3).
    a(4).
    { a(X) : b(X),c(X) ; d(X) : e(X),X=1..3 } =1 :- p(X).
    """
    graph_info, _ = get_sort_program_and_get_graph(program)
    g = nx.node_link_graph(graph_info[0])
    assert len(g.nodes) == 9
    assert len(g.edges) == 8


def test_negative_recursion_gets_treated_correctly(get_sort_program_and_get_graph):
    program = "a. b :- not c, a. c :- not b, a."
    graph_info, _ = get_sort_program_and_get_graph(program)
    g = nx.node_link_graph(graph_info[0])
    assert len(g.nodes) == 3
    assert len(g.edges) == 2


def test_path_creation(app_context):
    program = "fact(1). result(X) :- fact(X). next(X) :- fact(X)."
    transformed = transform(program)
    single_saved_model = get_stable_models_for_program(program).pop()
    facts, constants = [], []
    h_symbols = get_h_symbols_from_model(single_saved_model, transformed, facts, constants)
    rule_mapping = {1: Transformation(1, (parse_program_to_ast("fact(1)."),)), 2: Transformation(2, (parse_program_to_ast("result(X) :- fact(X)."),))}
    path = make_reason_path_from_facts_to_stable_model(single_saved_model,
                                                       rule_mapping, Node(frozenset(), 0),
                                                       h_symbols, frozenset())
    nodes, edges = list(path.nodes), list(t for _, _, t in path.edges.data(True))
    assert len(edges) == 2
    assert len(nodes) == 3
    assert all([isinstance(node, Node) for node in nodes])


def test_atoms_are_propagated_correctly_through_diffs(app_context):
    program = "a. b :- a. c :- b. d :- c."
    loc = Location(Position("str",1,1), Position("str",1,1))
    transformed = transform(program)
    single_saved_model = get_stable_models_for_program(program).pop()
    facts, constants = [], []
    h_symbols = get_h_symbols_from_model(single_saved_model, transformed, facts, constants)
    rule_mapping = {1: Transformation(1, (parse_program_to_ast("b :- a."),)), 2: Transformation(2, (parse_program_to_ast("c :- b."),)), 3: Transformation(3, (parse_program_to_ast("d :- c."),))}
    path = make_reason_path_from_facts_to_stable_model(single_saved_model,
                                                        rule_mapping,
                                                       Node(frozenset([SymbolIdentifier(Function(loc,"a",[], False))]), 0, frozenset([Function(loc,"a", [], False)])), # type: ignore
                                                       h_symbols, set())
    beginning: Node = get_start_node_from_graph(path)
    end: Node = get_end_node_from_path(path)
    path_list: List[Node] = nx.shortest_path(path, beginning, end) # type: ignore
    for src, tgt in pairwise(path_list):
        assert src.diff.issubset(tgt.atoms)
        assert len(src.atoms) == len(tgt.atoms) - len(tgt.diff)


def test_multiple_sortings_yield_input_order_first(load_analyzer):
    # uses all sorted programs
    program= """
    e. f. g.
    1 {a; b} 1.
    c :- a.
    c :- b.
    h. i.
    """
    analyzer = load_analyzer(program)
    sorted_programs = list(analyzer.get_sorted_program())
    assert len(sorted_programs) == 2
    # assert first sorting is closest to the original program
    assert sorted_programs[0][1] == Transformation(1, (parse_program_to_ast("c :- a."),))
    assert sorted_programs[0][2] == Transformation(2, (parse_program_to_ast("c :- b."),))
    assert sorted_programs[1][1] == Transformation(1, (parse_program_to_ast("c :- b."),))
    assert sorted_programs[1][2] == Transformation(2, (parse_program_to_ast("c :- a."),))


def test_multiple_sortings_yield_input_order_first_2(load_analyzer):
    program= """
    e. f. g.
    1 {a; b} 1.
    c :- b.
    c :- a.
    h. i.
    """
    analyzer = load_analyzer(program)
    sorted_programs = list(analyzer.get_sorted_program())
    assert len(sorted_programs) == 2
    # assert first sorting is closest to the original program
    assert sorted_programs[0][1] == Transformation(1, (parse_program_to_ast("c :- b."),))
    assert sorted_programs[0][2] == Transformation(2, (parse_program_to_ast("c :- a."),))
    assert sorted_programs[1][1] == Transformation(1, (parse_program_to_ast("c :- a."),))
    assert sorted_programs[1][2] == Transformation(2, (parse_program_to_ast("c :- b."),))

