from typing import List, Collection, Dict
from collections import defaultdict

import networkx as nx
from clingo.application import clingo_main, Application
from clingo.script import enable_python
from clingo import Symbol, Number

from .utils import insert_atoms_into_nodes, identify_reasons
from ..shared.model import Node, SymbolIdentifier
from ..shared.util import pairwise


class RecursionReasonsingApp(Application):

    def __init__(self, **kwargs):
        self.atoms = []
        self.init = kwargs.pop("init", [])
        self.program = kwargs.pop("program", "")
        self.register_h_symbols = kwargs.pop("callback", None)

    def new(self):
        return self.atoms

    def main(self, control, files):
        control.add("iter", ["n"], self.program)
        self.atoms = self.init

        step = 1
        while self.atoms != []:
            control.ground([("iter", [Number(step)])], context=self)
            self.atoms = [ x.symbol.arguments[1] for x in \
                            control.symbolic_atoms.by_signature("h", 4)
                           if x.is_fact and x.symbol.arguments[3].number == step
                         ]
            step += 1

        for x in control.symbolic_atoms.by_signature("h", 4):
            self.register_h_symbols(x.symbol)


def get_recursion_subgraph(facts, transformation, conflict_free_h):
    """
    Get a recursion explanation for the given facts and the recursive transformation.
    Generate graph from explanation, sorted by the iteration step number.
    """
    enable_python()
    init = [fact.symbol for fact in facts]

    justification_program = ""
    for i,rule in enumerate(transformation.rules):
        tupleified = ",".join(list(map(str,rule.body)))
        justification_head = f"{conflict_free_h}({i+1}, {rule.head}, ({tupleified}), n)"
        justification_body = ",".join(f"model({atom})" for atom in rule.body)
        justification_body += f", not model({rule.head})"

        justification_program += f"{justification_head} :- {justification_body}.\n"

    justification_program += "model(@new())."

    h_syms = set()
    if clingo_main( \
        RecursionReasonsingApp(init = init, program = justification_program, \
        callback = h_syms.add), []) == 0:

        h_syms = collect_h_symbols_and_create_nodes(h_syms)
        h_syms.sort(key=lambda node: node.rule_nr)
        insert_atoms_into_nodes(h_syms)
        
        reasoning_subgraph = nx.DiGraph()
        for a, b in pairwise(h_syms):
            reasoning_subgraph.add_edge(a, b)
        return reasoning_subgraph
    return False


def collect_h_symbols_and_create_nodes(h_symbols: Collection[Symbol]) -> List[Node]:
    """
    Collect all h symbols and create nodes for each iteration step.
    Adapted from the function for the same purpose on the main graph.
    """
    tmp_symbol: Dict[int, List[SymbolIdentifier]] = defaultdict(list)
    tmp_reason: Dict[int, Dict[Symbol, List[Symbol]]] = defaultdict(dict)

    for sym in h_symbols:
        _, symbol, reasons, iter_nr = sym.arguments
        tmp_symbol[iter_nr.number].append(symbol)
        tmp_reason[iter_nr.number][str(symbol)] = reasons.arguments
    for iter_nr in tmp_symbol.keys():
        tmp_symbol[iter_nr] = set(tmp_symbol[iter_nr])
        tmp_symbol[iter_nr] = map(SymbolIdentifier, tmp_symbol[iter_nr])

    h_symbols = [
        Node(frozenset(tmp_symbol[iter_nr]), iter_nr, reason=tmp_reason[iter_nr]) \
            if iter_nr in tmp_symbol else Node(frozenset(), iter_nr) 
            for iter_nr in range(1, max(tmp_symbol.keys()) + 1)]

    return h_symbols

