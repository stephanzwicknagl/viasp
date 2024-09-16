from itertools import tee
from typing import Any, TypeVar, Iterable, Tuple, List, Sequence, Dict
from collections import defaultdict
from types import MappingProxyType
from hashlib import sha1
from flask import current_app, session
from uuid import uuid4
import json
import jsonschema
from jsonschema import validate

from clingo.ast import ASTType, AST, parse_string
import jsonschema.exceptions
import networkx as nx
from ..exceptions import InvalidSyntax, InvalidSyntaxJSON
from .simple_logging import warn


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

def DefaultMappingProxyType() -> MappingProxyType:
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
            if len(n.recursive) > 0 and node in n.recursive:
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


clingo_json_schema = {
    "type": "object",
    "required": ["Call", "Result"],
    "properties": {
        "Call": {
            "type": "array",
        },
        "Result": {
            "type": "string",
        }
    }
}

def parse_clingo_json(json_str):
    """
    Parses a json string from the output of clingo obtained using the option ``--outf=2``.
    Expects a SATISFIABLE answer.

    Args:
        json_str (str): A string with the json

    Returns:
        (`list[str]`) A list with the programs as strings

    Raises:
        :py:class:`InvalidSyntax`: if the json format is invalid or is not a SAT result.
    """
    try:
        j = json.loads(json_str.encode())
        validate(instance=j, schema=clingo_json_schema)
        if not "Witnesses" in j["Call"][0]:
            witnesses = []
        else:
            witnesses = j["Call"][0]["Witnesses"]

        models_prgs = []
        for i, w in enumerate(witnesses):
            facts_str = "\n".join([f"{v}." for v in w["Value"]])
            output_str = " ".join([f"{v}" for v in w["Value"]])
            costs = w.get("Costs", [])
            models_prgs.append({"facts": facts_str, "representation": output_str, "number": i+1, "cost": costs})
        
        optimum = []
        if "Costs" in j["Models"]:
            optimum = j['Models']['Costs']

        return {"models": models_prgs, "unsatisfiable": j['Result'] == 'UNSATISFIABLE', "optimum": optimum}

    except json.JSONDecodeError as e:
        raise InvalidSyntax('The json can not be read.', str(e)) from None
    except jsonschema.exceptions.ValidationError as e:
        raise InvalidSyntaxJSON(
            'The json does not have the expected structure. Make sure you used the -outf=2 option in clingo.',
            str(e)) from None


def get_json(files, stdin):
    """
    Gets the json from the arguments, in case one is provided
    Also returns boolean indicating if the json was provided as stdin
    """
    json_str = None

    for f in files:
        if ".json" not in f[1]:
            continue
        if json_str is not None:
            raise ValueError("Only one json file can be provided")
        json_str = f[2].read()
    try:
        prg_list = parse_clingo_json(stdin)
        if json_str is not None:
            raise ValueError("Only one json can be provided as input.")
        return prg_list, True
    except InvalidSyntaxJSON as e:
        raise e from None
    except InvalidSyntax:
        if json_str is None:
            return None, False
        try:
            prg_list = parse_clingo_json(json_str)
            return prg_list, False
        except InvalidSyntaxJSON as e:
            raise e from None
        except InvalidSyntax as e:
            return None, False


def get_lp_files(files, stdin, stdin_is_json=False):
    """
    Gets the lp program paths from the arguments, raises error if non is provided and no stdin is provided
    """
    lp_files = []

    for f in files:
        if ".lp" not in f[1]:
            continue
        lp_files.append(f)
    if lp_files == []:
        if stdin == "" or stdin_is_json:
            raise ValueError(
                "No ASP encoding provided, no output will be produced by viasp"
            )
        lp_files.append(("stdin", "-"))
    return lp_files


def get_optimal_models(models: Dict) -> Dict:
    if len(models) == 0:
        return {}
    number_of_opt_vars = len(next(iter(models.values()))) 
    for i in range(number_of_opt_vars):
        values_at_index_i = list(map(lambda opt_value_list: opt_value_list[i], models.values()))
        minimum_at_index_i = min(values_at_index_i)

        to_be_removed = []

        for model, model_opt_value in models.items():
            if model_opt_value[i] != minimum_at_index_i:
                to_be_removed.append(model)
        
        for model in to_be_removed:
            models.pop(model, None)
    return models

class SolveHandle:
    class Unsat:
        def __init__(self, unsat):
            self.unsatisfiable = unsat

        def __str__(self):
            if self.unsatisfiable:
                return "UNSAT"
            else:
                return "SAT"

    def __init__(self, data):
        self.data = data

    def __iter__(self):
        return iter(self.data['models'])

    def __enter__(self):
        # Set up resources here
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Tear down resources here
        pass
    
    def opt(self):
        return self.data["optimum"]

    def get(self):
        return self.Unsat(self.data['unsatisfiable'])
