"""Mostly graph utility functions."""
import networkx as nx
from clingo.ast import Rule, ASTType
from typing import List, Sequence
from ..shared.simple_logging import warn


def is_constraint(rule: Rule):
    return rule.ast_type == ASTType.Rule and "atom" in rule.head.child_keys and rule.head.atom.ast_type == ASTType.BooleanConstant


def merge_constraints(g: nx.Graph) -> nx.Graph:
    mapping = {}
    constraints = frozenset([ruleset for ruleset in g.nodes for rule in ruleset if is_constraint(rule)])
    if constraints:
        merge_node = merge_nodes(constraints)
        mapping = {c: merge_node for c in constraints}
    return nx.relabel_nodes(g, mapping)


def merge_cycles(g: nx.Graph) -> nx.Graph:
    mapping = {}
    for cycle in nx.algorithms.components.strongly_connected_components(g):
        merge_node = merge_nodes(cycle)
        mapping.update({old_node: merge_node for old_node in cycle})
    # which nodes were merged
    where_recursion_happens = set()
    for k,v in mapping.items():
        if k != v:
            where_recursion_happens.add(merge_node)
    return nx.relabel_nodes(g, mapping), frozenset(where_recursion_happens)


def merge_nodes(nodes: frozenset) -> frozenset:
    old = set()
    for x in nodes:
        old.update(x)
    return frozenset(old)


def remove_loops(g: nx.Graph) -> nx.Graph:
    remove_edges = []
    where_recursion_happens = set()
    for edge in g.edges:
        u, v = edge
        if u == v:
            remove_edges.append(edge)
            # info on which node's loop is removed
            where_recursion_happens.add(u)

    for edge in remove_edges:
        g.remove_edge(*edge)
    return g, frozenset(where_recursion_happens)

def topological_sort(g: nx.DiGraph, rules: Sequence[Rule]) -> List:
    """ Topological sort of the graph.
        If the order is ambiguous, prefer the order of the rules.
        Note: Rule = Node

        :param g: Graph
        :param rules: List of Rules
    """
    sorted: List = []        # L list of the sorted elements
    no_incoming_edge = set() # set of all nodes with no incoming edges

    no_incoming_edge.update([node for node in g.nodes if g.in_degree(node) == 0])
    while len(no_incoming_edge):
        earliest_node_index = len(rules)
        earliest_node = None
        for node in no_incoming_edge:
            for rule in node:
                # with open("t.log", "a") as f:
                #     f.write(f"Node:\n     {node}\n\n")
                #     f.write(f"Rules:\n     {rules}\n\n")
                node_index = rules.index(rule)
                if node_index<earliest_node_index:
                    earliest_node_index=node_index
                    earliest_node = node

        no_incoming_edge.remove(earliest_node)
        sorted.append(earliest_node)

        # update graph
        for node in list(g.successors(earliest_node)):
            g.remove_edge(earliest_node, node)
            if g.in_degree(node)==0:
                no_incoming_edge.add(node)

    if len(g.edges):
        warn("Could not sort the graph.")
        raise Exception("Could not sort the graph.")
    return sorted
