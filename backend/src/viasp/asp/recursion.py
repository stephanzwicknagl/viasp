from typing import List, Collection, Dict, Union
from collections import defaultdict

import networkx as nx
from clingo.script import enable_python
from clingo import Symbol, Number, Control
from clingo.ast import AST

from .utils import insert_atoms_into_nodes
from ..shared.model import Node, SymbolIdentifier
from ..shared.util import pairwise


class RecursionReasoner:

    def __init__(self, **kwargs):
        self.atoms = []
        self.init = kwargs.pop("init", [])
        self.program = kwargs.pop("program", "")
        self.register_h_symbols = kwargs.pop("callback", None)
        self.conflict_free_h = kwargs.pop("conflict_free_h", "h")

    def new(self):
        return self.atoms

    def main(self):
        control = Control()
        control.add("iter", ["n"], self.program)
        self.atoms = self.init

        step = 1
        while self.atoms != []:
            control.ground([("iter", [Number(step)])], context=self)
            self.atoms = [ x.symbol.arguments[1] for x in
                            control.symbolic_atoms.by_signature(self.conflict_free_h, 4)
                           if x.is_fact and x.symbol.arguments[3].number == step
                         ]
            step += 1

        for x in control.symbolic_atoms.by_signature(self.conflict_free_h, 4):
            self.register_h_symbols(x.symbol)


def get_recursion_subgraph(facts: frozenset, supernode_symbols: frozenset,
                        transformation: Union[AST, str], conflict_free_h: str):
    """
    Get a recursion explanation for the given facts and the recursive transformation.
    Generate graph from explanation, sorted by the iteration step number.

    :param facts: The symbols that were true before the recursive node.
    :param supernode_symbols: The SymbolIdentifiers of the recursive node.
    :param transformation: The recursive transformation. An ast object.
    :param conflict_free_h: The name of the h predicate.
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
    try:
        RecursionReasoner(init = init,
                            program = justification_program,
                            callback = h_syms.add,
                            conflict_free_h = conflict_free_h).main()
    except RuntimeError:
        return False

    h_syms = collect_h_symbols_and_create_nodes(h_syms, supernode_symbols)
    h_syms.sort(key=lambda node: node.rule_nr) # here: rule_nr is iteration number
    h_syms.insert(0, Node(frozenset(facts), -1))
    insert_atoms_into_nodes(h_syms)

    reasoning_subgraph = nx.DiGraph()
    for a, b in pairwise(h_syms[1:]):
        reasoning_subgraph.add_edge(a, b)
    return reasoning_subgraph if reasoning_subgraph.size() != 0 else False 


def collect_h_symbols_and_create_nodes(h_symbols: Collection[Symbol], supernode_symbols: frozenset) -> List[Node]:
    """
    Collect all h symbols and create nodes for each iteration step.
    Adapted from the function for the same purpose on the main graph.
    iter_nr is the reference to which iteration of the recursive node the symbol belongs to. 
        It is used similarly to the rule_nr in the main graph.
    The SymbolIdentifiers are copied from the supernode_symbols to keep the UUIDs consistent.

    :param h_symbols: The h symbols of the recursive node.
    :param supernode_symbols: The supernode_symbols are the symbols of the recursive node. 
        They are used to keep the SymbolIdentifiers' UUIDs consistent.  
    """
    tmp_symbol: Dict[int, List[SymbolIdentifier]] = defaultdict(list)
    tmp_reason: Dict[int, Dict[Symbol, List[Symbol]]] = defaultdict(dict)

    for sym in h_symbols:
        _, symbol, reasons, iter_nr = sym.arguments
        tmp_symbol[iter_nr.number].append(symbol)
        tmp_reason[iter_nr.number][str(symbol)] = reasons.arguments
    for iter_nr in tmp_symbol.keys():
        tmp_symbol[iter_nr] = set(tmp_symbol[iter_nr])
        tmp_symbol[iter_nr] = map(lambda symbol: next(filter(
                lambda supernode_symbol: supernode_symbol==symbol, supernode_symbols)) if
                symbol in supernode_symbols else SymbolIdentifier(symbol),
                tmp_symbol[iter_nr])

    h_symbols = [
        Node(frozenset(tmp_symbol[iter_nr]), iter_nr, reason=tmp_reason[iter_nr])
            if iter_nr in tmp_symbol else Node(frozenset(), iter_nr) 
            for iter_nr in range(1, max(tmp_symbol.keys(), default=-1) + 1)]

    return h_symbols

