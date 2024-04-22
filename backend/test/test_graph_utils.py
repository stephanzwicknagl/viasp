from typing import Dict, Tuple, Set

import networkx as nx
from viasp.asp.utils import topological_sort
from viasp.asp.reify import ProgramAnalyzer
from viasp.server.database import GraphAccessor, get_or_create_encoding_id
from viasp.shared.model import RuleContainer

def test_topological_sort():
    g = nx.DiGraph()
    rules = ["{b(X)} :- a(X).", "c(X) :- a(X)."]
    rules_container = [RuleContainer(str_=tuple([r])) for r in rules]
    head_dependencies: Dict[Tuple[str, int], Set] = {
        ("b", 1): {"{b(X)} :- a(X)."},
        ("c", 1): {"c(X) :- a(X)."},
    }
    body_dependencies: Dict[Tuple[str, int], Set] = {
        ("a", 1): {"{b(X)} :- a(X)."},
        ("a", 1): {"{b(X)} :- a(X)."},
    }

    for deps in head_dependencies.values():
        for dep in deps:
            g.add_node(RuleContainer(str_=tuple([dep])))
    for deps in body_dependencies.values():
        for dep in deps:
            g.add_node(RuleContainer(str_=tuple([dep])))

    for head_signature, rules_with_head in head_dependencies.items():
        dependent_rules = body_dependencies.get(head_signature, [])
        for parent_rule in rules_with_head:
            for dependent_rule in dependent_rules:
                g.add_edge(RuleContainer(str_=tuple([parent_rule])), RuleContainer(str_=tuple([dependent_rule])))

    sorted = topological_sort(g, [r.ast[0] for r in rules_container])
    assert len(sorted) == len(rules)
    for i in range(len(rules)):
        assert sorted[i] == rules_container[i]


def test_topological_sort_2():
    g = nx.DiGraph()
    rules = ["x:-y.",
             "e:-x.",
             "z:-x.",
             "d:-z.",
             "a:-x,z.",
             "b:-z.",
             "c:-b,a."]
    rules_container = [RuleContainer(str_=tuple([r])) for r in rules]
    head_dependencies: Dict[Tuple[str, int], Set] = {
        ("x", 0): {"x:-y."},
        ("e", 0): {"e:-x."},
        ("z", 0): {"z:-x."},
        ("d", 0): {"d:-z."},
        ("a", 0): {"a:-x,z."},
        ("b", 0): {"b:-z."},
        ("c", 0): {"c:-b,a."},
    }
    body_dependencies: Dict[Tuple[str, int], Set] = {
        ("y", 0): {"x:-y."},
        ("x", 0): {"e:-x.", "z:-x.", "a:-x,z."},
        ("z", 0): {"d:-z.", "a:-x,z.", "b:-z."},
        ("b", 0): {"c:-b,a."},
    }

    for deps in head_dependencies.values():
        for dep in deps:
            g.add_node(RuleContainer(str_=tuple([dep])))
    for deps in body_dependencies.values():
        for dep in deps:
            g.add_node(RuleContainer(str_=tuple([dep])))

    for head_signature, rules_with_head in head_dependencies.items():
        dependent_rules = body_dependencies.get(head_signature, [])
        for parent_rule in rules_with_head:
            for dependent_rule in dependent_rules:
                g.add_edge(RuleContainer(str_=tuple([parent_rule])), RuleContainer(str_=tuple([dependent_rule])))

    sorted = topological_sort(g, [r.ast[0] for r in rules_container])
    assert len(sorted) == len(rules)
    for i in range(len(rules)):
        assert sorted[i] == rules_container[i]

def test_adjacent_sorts(app_context):
    rules = ["{b(X)} :- a(X).", "c(X) :- a(X)."]
    GraphAccessor().save_program('\n'.join(rules), get_or_create_encoding_id())
    analyzer = ProgramAnalyzer()
    sorted, g = analyzer.sort('\n'.join(rules))

    adjacent_sorts = analyzer.get_index_mapping_for_adjacent_topological_sorts(sorted)
    assert len(adjacent_sorts) == 1


def test_adjacent_sorts_2():
    rules = ["x:-y.",
             "e:-x.",
             "z:-x.",
             "d:-z.",
             "a:-x,z.",
             "b:-z.",
             "c:-b,a."]
    analyzer = ProgramAnalyzer()
    sorted, g = analyzer.get_sort_program_and_graph('\n'.join(rules))

    adjacent_sorts = find_adjacent_topological_sorts(g, sorted)
    assert len(adjacent_sorts) == 10
