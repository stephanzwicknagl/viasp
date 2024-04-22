from itertools import tee
from typing import Any, TypeVar, Iterable, Tuple, List, Sequence
from collections import defaultdict
from types import MappingProxyType
from hashlib import sha1
from flask import current_app, session
from uuid import uuid4

from clingo.ast import ASTType, AST, parse_string
import networkx as nx


def get_start_node_from_graph(graph: nx.DiGraph) -> Any:
    if graph.number_of_nodes() == 0:
        raise ValueError("Graph is empty")
    beginning = next(filter(lambda tuple: tuple[1] == 0, graph.in_degree()))
    return beginning[0]


def get_end_node_from_path(graph: nx.DiGraph) -> Any:
    end = next(filter(lambda tuple: tuple[1] == 0, graph.out_degree()))
    return end[0]


def get_leafs_from_graph(graph: nx.DiGraph) -> Iterable[Any]:
    for candidate, out_degree in graph.out_degree:
        if out_degree == 0:
            yield candidate

def get_root_node_from_graph(graph: nx.DiGraph) -> Any:
    try:
        return next(nx.topological_sort(graph))
    except StopIteration:
        raise ValueError("Graph is empty")

def get_sorted_path_from_path_graph(graph: nx.DiGraph) -> Any:
    start = get_start_node_from_graph(graph)
    end = get_end_node_from_path(graph)
    return nx.shortest_path(graph, start, end)


T = TypeVar("T")


def pairwise(iterable: Iterable[T]) -> Iterable[Tuple[T, T]]:
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

def DefaultMappingProxyType() -> MappingProxyType[str, List]:
    return MappingProxyType(defaultdict())

def is_recursive(node, graph):
    """
    Checks if the node is recursive.
    :param node: The node to check.
    :param graph: The graph that contains the node.
    :return: True if the node is recursive, False otherwise.
    """
    nn = set(graph.nodes)
    if node in nn:
        return False
    else:
        for n in nn:
            if n.recursive != False and node in set(n.recursive.nodes):
                return True


def hash_from_sorted_transformations(sorted_program: List) -> str:
    hashes = [s.hash for s in sorted_program]
    concatenated = "".join(hashes)
    hash_object = sha1(concatenated.encode())
    return hash_object.hexdigest()

def hash_transformation_rules(rules: Tuple[Any, ...]) -> str:
    hash_object = sha1()
    for rule in rules:
        rule_str = current_app.json.dumps(rule)
        rule_hash = sha1(rule_str.encode()).hexdigest()
        hash_object.update(rule_hash.encode())
    return hash_object.hexdigest()


def get_rules_from_input_program(rules: Tuple) -> Sequence[str]:
    from ..server.database import get_database, get_or_create_encoding_id
    
    rules_from_input_program: Sequence[str] = []
    encoding_id = get_or_create_encoding_id()
    db = get_database()
    program = db.load_program(encoding_id).split("\n")
    for rule in rules:
        if isinstance(rule, str):
            rules_from_input_program.append(rule)
            continue
        begin_line = rule.location.begin.line
        begin_colu = rule.location.begin.column
        end_line = rule.location.end.line
        end_colu = rule.location.end.column
        r = ""
        if begin_line != end_line:
            r += program[begin_line - 1][begin_colu-1:] + "\n"
            for i in range(begin_line, end_line - 1):
                r += program[i] + "\n"
            r += program[end_line - 1][:end_colu]
        else:
            r += program[begin_line - 1][begin_colu - 1:end_colu-1]
        r = append_hashtag_to_minimize(r, rule, program, begin_line, begin_colu)
        rules_from_input_program.append(r)
    return rules_from_input_program


def append_hashtag_to_minimize(r: str, rule: AST, program: Sequence[str], begin_line: int, begin_colu: int) -> str:
    if rule.ast_type == ASTType.Minimize and r[:2] != ":~":
        for i in range(begin_line, 0, -1):
            colu_of_hashtag = program[i - 1].rfind("#")
            if colu_of_hashtag != -1:
                if begin_line != i:
                    pre = program[i - 1][colu_of_hashtag:] + "\n"
                    for k in range(i, begin_line-1):
                        pre += program[k] + "\n"
                    pre += program[begin_line][:begin_colu-1]
                    r = pre + r + "}."
                else:
                    r = program[i - 1][colu_of_hashtag:begin_colu-1] + r + "}."
                break
    return r

def get_ast_from_input_string(rules_str: Tuple[str, ...]) -> Tuple[AST, ...]:
    rules_ast = []
    for rule in rules_str:
        parse_string(
            rule, lambda rule: rules_ast.append(rule)
            if rule.ast_type != ASTType.Program else None)
    return tuple(rules_ast)