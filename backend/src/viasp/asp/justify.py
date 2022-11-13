"""This module is concerned with finding reasons for why a stable model is found."""
from collections import defaultdict
from typing import List, Collection, Dict, Iterable, Union

import networkx as nx

from clingo import Control, Symbol, Model

from clingo.ast import AST, Function
from networkx import DiGraph

from .reify import ProgramAnalyzer
from ..shared.model import Node, Transformation
from ..shared.simple_logging import info, warn
from ..shared.util import pairwise, get_leafs_from_graph


def stringify_fact(fact: Function) -> str:
    return f"{str(fact)}."


def get_h_symbols_from_model(wrapped_stable_model: Iterable[Symbol],
                             transformed_prg: Collection[Union[str, AST]],
                             facts: List[Symbol],
                             constants: List[Symbol],
                             h="h") -> List[Symbol]:
    rules_that_are_reasons_why = []
    ctl = Control()
    stringified = "".join(map(str, transformed_prg))
    ctl.add("base", [], "".join(map(str, constants)))
    ctl.add("base", [], "".join(map(stringify_fact, facts)))
    ctl.add("base", [], stringified)
    ctl.add("base", [], "".join(map(str, wrapped_stable_model)))
    ctl.ground([("base", [])])
    for x in ctl.symbolic_atoms.by_signature(h, 3):
        rules_that_are_reasons_why.append(x.symbol)
    return rules_that_are_reasons_why


def get_facts(original_program) -> Collection[Symbol]:
    ctl = Control()
    facts = set()
    as_string = "".join(map(str, original_program))
    ctl.add("__facts", [], as_string)
    ctl.ground([("__facts", [])])
    for atom in ctl.symbolic_atoms:
        if atom.is_fact:
            facts.add(atom.symbol)
    return frozenset(facts)


def collect_h_symbols_and_create_nodes(h_symbols: Collection[Symbol], relevant_indices, pad: bool) -> List[Node]:
    tmp: Dict[int, List[Symbol]] = defaultdict(list)
    for sym in h_symbols:
        rule_nr, symbol, _ = sym.arguments
        tmp[rule_nr.number].append(symbol)
    if pad:
        h_symbols = [
            Node(frozenset(tmp[rule_nr]), rule_nr) if rule_nr in tmp else Node(frozenset(), rule_nr) for
            rule_nr in relevant_indices]
    else:
        h_symbols = [Node(frozenset(tmp[rule_nr]), rule_nr) for rule_nr in tmp.keys()]

    return h_symbols


def insert_atoms_into_nodes(path: List[Node]) -> None:
    facts = path[0]
    state = set(facts.diff)
    facts.atoms = frozenset(state)
    for u, v in pairwise(path):
        state.update(v.diff)
        state.update(u.diff)
        v.atoms = frozenset(state)


def make_reason_path_from_facts_to_stable_model(wrapped_stable_model, rule_mapping: Dict[int, Union[AST, str]],
                                                fact_node: Node, h_syms, pad=True) -> nx.DiGraph:
    h_syms = collect_h_symbols_and_create_nodes(h_syms, rule_mapping.keys(), pad)
    h_syms.sort(key=lambda node: node.rule_nr)
    h_syms.insert(0, fact_node)

    insert_atoms_into_nodes(h_syms)
    g = nx.DiGraph()
    if len(h_syms) == 1:
        # If there is a stable model that is exactly the same as the facts.
        warn(f"Adding a model without reasons {wrapped_stable_model}")
        g.add_edge(fact_node, Node(frozenset(), min(rule_mapping.keys()), frozenset(fact_node.diff)),
                   transformation=rule_mapping[min(rule_mapping.keys())])
        return g

    for a, b in pairwise(h_syms):
        g.add_edge(a, b, transformation=rule_mapping[b.rule_nr])

    return g


def join_paths_with_facts(paths: Collection[nx.DiGraph]) -> nx.DiGraph:
    combined = nx.DiGraph()
    for path in paths:
        for node in path.nodes():
            if node not in combined.nodes:
                combined.add_node(node)
        for u, v, r in path.edges(data=True):
            if u in combined.nodes and v in combined.nodes:
                combined.add_edge(u, v, transformation=r["transformation"])
    return combined


def make_transformation_mapping(transformations: Iterable[Transformation]):
    return {t.id: t for t in transformations}


def append_noops(result_graph: DiGraph, analyzer: ProgramAnalyzer):
    next_transformation_id = max(t.id for t in analyzer.get_sorted_program()) + 1
    leaves = list(get_leafs_from_graph(result_graph))
    leaf: Node
    for leaf in leaves:
        noop_node = Node(frozenset(), next_transformation_id, leaf.atoms)
        result_graph.add_edge(leaf, noop_node,
                              transformation=Transformation(next_transformation_id,
                                                            [str(pt) for pt in analyzer.pass_through]))


def build_graph(wrapped_stable_models: Collection[str], transformed_prg: Collection[AST],
                analyzer: ProgramAnalyzer) -> nx.DiGraph:
    paths: List[nx.DiGraph] = []
    facts = analyzer.get_facts()
    sorted_program = analyzer.get_sorted_program()
    mapping = make_transformation_mapping(sorted_program)
    fact_node = Node(frozenset(facts), -1, frozenset(facts))
    if not len(mapping):
        info(f"Program only contains facts. {fact_node}")
        single_node_graph = nx.DiGraph()
        single_node_graph.add_node(fact_node)
        return single_node_graph
    for model in wrapped_stable_models:
        h_symbols = get_h_symbols_from_model(model, transformed_prg, facts, analyzer.get_constants(),
                                             analyzer.get_conflict_free_h())
        new_path = make_reason_path_from_facts_to_stable_model(model, mapping, fact_node, h_symbols)
        paths.append(new_path)

    result_graph = join_paths_with_facts(paths)
    if analyzer.pass_through:
        append_noops(result_graph, analyzer)
    return result_graph


def save_model(model: Model) -> Collection[str]:
    wrapped = []
    for part in model.symbols(atoms=True):
        wrapped.append(f"model({part}).")
    return wrapped
