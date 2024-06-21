from os.path import join, dirname, abspath
import sqlite3
from typing import Set, List, Union, Tuple, Optional, Sequence
from uuid import UUID
from flask import current_app, g
import networkx as nx
import pickle

from clingo.ast import Transformer

from ..shared.defaults import PROGRAM_STORAGE_PATH, GRAPH_PATH
from ..shared.event import Event, subscribe
from ..shared.model import ClingoMethodCall, StableModel, Transformation, TransformerTransport, TransformationError



class ProgramDatabase:

    def __init__(self, path=PROGRAM_STORAGE_PATH):
        self.path: str = join(dirname(abspath(__file__)), path)

    def get_program(self):
        prg = ""
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                prg = "".join(f.readlines())
        except FileNotFoundError:
            self.save_program("")
        return prg

    def add_to_program(self, program: str):
        current = self.get_program()
        current = current + program
        self.save_program(current)

    def save_program(self, program: str):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(program)  #.split("\n"))

    def clear_program(self):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("")


class CallCenter:

    def __init__(self):
        self.calls: List[ClingoMethodCall] = []
        self.used: Set[UUID] = set()
        subscribe(Event.CALL_EXECUTED, self.mark_call_as_used)

    def append(self, call: ClingoMethodCall):
        self.calls.append(call)

    def extend(self, calls: List[ClingoMethodCall]):
        self.calls.extend(calls)

    def get_all(self) -> List[ClingoMethodCall]:
        return self.calls

    def get_pending(self) -> List[ClingoMethodCall]:
        return list(filter(lambda call: call.uuid not in self.used,
                           self.calls))

    def mark_call_as_used(self, call: ClingoMethodCall):
        self.used.add(call.uuid)

def get_or_create_encoding_id() -> str:
    # TODO
    # if 'encoding_id' not in session:
    #     session['encoding_id'] = uuid4().hex
    # print(f"Returing encoding id {session['encoding_id']}", flush=True)
    # return session['encoding_id']
    return "0"

class GraphAccessor:

    def __init__(self):
        self.dbpath = join(dirname(abspath(__file__)), GRAPH_PATH)
        self.conn = sqlite3.connect(self.dbpath)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS encodings (
                id TEXT PRIMARY KEY,
                program TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                encoding_id TEXT,
                model TEXT,
                FOREIGN KEY (encoding_id) REFERENCES encodings(id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS graphs (
                hash TEXT PRIMARY KEY,
                data TEXT,
                sort TEXT NOT NULL,
                encoding_id TEXT,
                FOREIGN KEY (encoding_id) REFERENCES encodings(id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS current_graph (
                hash TEXT PRIMARY KEY,
                encoding_id TEXT,
                FOREIGN KEY(hash) REFERENCES graphs(hash)
                FOREIGN KEY(encoding_id) REFERENCES encodings(id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS graph_relations (
                graph_hash_1 TEXT,
                graph_hash_2 TEXT,
                encoding_id TEXT,
                PRIMARY KEY (graph_hash_1, graph_hash_2),
                FOREIGN KEY(graph_hash_1) REFERENCES graphs(hash),
                FOREIGN KEY(graph_hash_2) REFERENCES graphs(hash)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS dependency_graph (
                    encoding_id TEXT PRIMARY KEY,
                    data TEXT,
                    FOREIGN KEY(encoding_id) REFERENCES encodings(id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS recursion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                encoding_id TEXT,
                recursive_hash TEXT,
                FOREIGN KEY(encoding_id) REFERENCES encodings(id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS clingraph (
                filename TEXT PRIMARY KEY,
                encoding_id TEXT,
                FOREIGN KEY(encoding_id) REFERENCES encodings(id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transformer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transformer BLOB,
                encoding_id TEXT,
                FOREIGN KEY(encoding_id) REFERENCES encodings(id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                encoding_id TEXT,
                warning TEXT,
                FOREIGN KEY(encoding_id) REFERENCES encodings(id)
            )
        """)
        self.conn.commit()

    # # # # # # #
    # ENCODING  #
    # # # # # # #

    def save_program(self, program: str, encoding_id: str):
        self.cursor.execute(
            """
            INSERT OR REPLACE INTO encodings (program, id) VALUES (?, ?)
        """, (program, encoding_id))
        self.conn.commit()

    def add_to_program(self, program: str, encoding_id: str):
        program = self.load_program(encoding_id) + program
        self.cursor.execute(
            """
            INSERT OR REPLACE INTO encodings (id, program) VALUES (?, ?)
        """, (encoding_id, program))
        self.conn.commit()

    def load_program(self, encoding_id: str) -> str:
        self.cursor.execute(
            """
            SELECT program FROM encodings WHERE id = (?)
        """, (encoding_id, ))
        result = self.cursor.fetchone()
        return result[0] if result is not None else ""

    def clear_program(self, encoding_id: str):
        self.cursor.execute(
            """
            DELETE FROM encodings WHERE id = (?)
        """, (encoding_id, ))
        self.conn.commit()

    # # # # # # #
    #  MODELS   #
    # # # # # # #

    def set_models(self, parsed_models: Sequence[Union[StableModel, str]],
                   encoding_id: str):
        self.clear_models(encoding_id)
        for model in parsed_models:
            json_model = current_app.json.dumps(model)
            self.cursor.execute(
                """
                INSERT INTO models (encoding_id, model) VALUES (?, ?)
            """, (encoding_id, json_model))
        self.conn.commit()

    def load_models(self, encoding_id: str) -> List[StableModel]:
        self.cursor.execute(
            """
            SELECT model FROM models WHERE encoding_id = (?)
        """, (encoding_id, ))
        result = self.cursor.fetchall()

        return [current_app.json.loads(r[0]) for r in result]

    def clear_models(self, encoding_id: str):
        self.cursor.execute(
            """
            DELETE FROM models WHERE encoding_id = (?)
        """, (encoding_id, ))
        self.conn.commit()

    # # # # # # # #
    #    GRAPHS   #
    # # # # # # # #

    def save_graph(self, graph: nx.Graph, hash: str,
                   sort: List[Transformation], encoding_id: str):
        self.cursor.execute(
            """
            INSERT OR REPLACE INTO graphs (data, hash, sort, encoding_id) VALUES (?, ?, ?, ?)
        """, (current_app.json.dumps(nx.node_link_data(graph)), hash,
              current_app.json.dumps(sort), encoding_id))
        self.conn.commit()

    def set_current_graph(self, hash: str, encoding_id: str):
        self.cursor.execute(
            """
            DELETE FROM current_graph WHERE encoding_id = (?)
        """, (encoding_id, ))
        self.cursor.execute(
            "INSERT INTO current_graph (hash, encoding_id) VALUES (?, ?)",
            (hash, encoding_id))
        self.conn.commit()

    def get_current_graph_hash(self, encoding_id: str) -> str:
        self.cursor.execute(
            """
            SELECT hash FROM current_graph WHERE encoding_id = (?)
        """, (encoding_id, ))
        result = self.cursor.fetchone()
        if result and result[0]:
            return result[0]
        return ""

    def load_graph_json(self, hash: str, encoding_id: str) -> str:
        self.cursor.execute(
            """
            SELECT data FROM graphs WHERE hash = ? AND encoding_id = ?
        """, (hash, encoding_id))
        result = self.cursor.fetchone()
        if not result:
            raise KeyError("The hash is not in the database")
        if result and result[0]:
            return result[0]
        raise ValueError("No graph found")

    def load_graph(self, hash: str, encoding_id: str) -> nx.DiGraph:
        graph_json_str = self.load_graph_json(hash, encoding_id)
        return nx.node_link_graph(current_app.json.loads(graph_json_str))

    def load_current_graph_json(self, encoding_id: str) -> str:
        hash = self.get_current_graph_hash(encoding_id)
        return self.load_graph_json(hash, encoding_id)

    def load_current_graph(self, encoding_id: str) -> nx.DiGraph:
        graph_json_str = self.load_current_graph_json(encoding_id)
        return nx.node_link_graph(current_app.json.loads(graph_json_str))

    # # # # # # # #
    #   SORTS     #
    # # # # # # # #

    def save_many_sorts(self, sorts: List[Tuple[str, List[Transformation],
                                                str]]):
        self.cursor.executemany(
            """
            INSERT OR REPLACE INTO graphs (hash, data, sort, encoding_id) VALUES (?, ?, ?, ?)
        """, [(hash, None, current_app.json.dumps(sort), encoding_id)
              for hash, sort, encoding_id in sorts])
        self.conn.commit()

    def save_sort(self, hash: str, sort: List[Transformation],
                  encoding_id: str):
        self.cursor.execute(
            """
            INSERT OR REPLACE INTO graphs (hash, data, sort, encoding_id) VALUES (?, ?, ?, ?)
        """, (hash, None, current_app.json.dumps(sort), encoding_id))
        self.conn.commit()

    def get_current_sort(self, encoding_id: str) -> List[Transformation]:
        hash = self.get_current_graph_hash(encoding_id)
        self.cursor.execute(
            """
            SELECT sort FROM graphs WHERE hash = ?
        """, (hash, ))
        result = self.cursor.fetchone()
        if result and result[0]:
            loaded = current_app.json.loads(result[0])
            loaded.sort(key=lambda x: x.id)
            return loaded 
        raise ValueError("No sort found")

    def load_all_sorts(self, encoding_id: str) -> List[str]:
        self.cursor.execute(
            """
            SELECT hash FROM graphs WHERE encoding_id = (?)
        """, (encoding_id, ))
        result: List[str] = self.cursor.fetchall()
        loaded_sorts: List[str] = [r[0] for r in result]
        current_sort_hash = self.get_current_graph_hash(encoding_id)
        if current_sort_hash != "":
            try:
                index_of_current_sort: int = loaded_sorts.index(
                    current_sort_hash)
                loaded_sorts = loaded_sorts[
                    index_of_current_sort:] + loaded_sorts[:
                                                           index_of_current_sort]
            except ValueError:
                pass
        return loaded_sorts

    def insert_graph_adjacency(self, hash1: str, hash2: str,
                              sort2: List[Transformation], encoding_id: str):
        self.cursor.execute("SELECT hash FROM graphs WHERE hash = ?",
                            (hash2, ))
        result = self.cursor.fetchone()

        if result is None:
            self.save_sort(hash2, sort2, encoding_id)
        self.insert_graph_adjacency_element(hash1, hash2, encoding_id)
        self.insert_graph_adjacency_element(hash2, hash1, encoding_id)
        self.conn.commit()

    def insert_graph_adjacency_element(self, hash1: str, hash2: str, encoding_id: str):
        try:
            self.cursor.execute(
                """
                INSERT INTO graph_relations (graph_hash_1, graph_hash_2, encoding_id) VALUES (?, ?, ?)
            """, (hash1, hash2, encoding_id))
        except sqlite3.IntegrityError:
            pass

    def save_dependency_graph(self, data: nx.DiGraph, encoding_id: str):
        self.cursor.execute(
            """
            INSERT OR REPLACE INTO dependency_graph (data, encoding_id) VALUES (?, ?)
        """, (current_app.json.dumps(nx.node_link_data(data)), encoding_id))
        self.conn.commit()

    def load_dependency_graph(self, encoding_id: str) -> nx.DiGraph:
        self.cursor.execute(
            """
            SELECT data FROM dependency_graph WHERE encoding_id = (?)
        """, (encoding_id, ))
        result = self.cursor.fetchone()
        if result and result[0]:
            return nx.node_link_graph(current_app.json.loads(result[0]))
        raise ValueError("No dependency graph found")

    def get_adjacent_graphs_hashes(self, hash: str,
                                  encoding_id: str) -> List[str]:
        self.cursor.execute(
            """
            SELECT graph_hash_2 FROM graph_relations WHERE graph_hash_1 = ? AND encoding_id = ?
        """, (hash, encoding_id))
        result = self.cursor.fetchall()
        return [r[0] for r in result]

    def clear_all_sorts(self, encoding_id: str):
        self.cursor.execute(
            """
            DELETE FROM graphs WHERE encoding_id = (?)
        """, (encoding_id, ))
        self.conn.commit()

    # # # # # # # #
    #  RECURSION  #
    # # # # # # # #

    def save_recursive_transformations_hashes(self, transformations: Set[str],
                                              encoding_id: str):
        for t in transformations:
            self.cursor.execute(
                """
                INSERT INTO recursion (encoding_id, recursive_hash) VALUES (?, ?)
            """, (encoding_id, t))
        self.conn.commit()

    def load_recursive_transformations_hashes(self,
                                              encoding_id: str) -> Set[str]:
        self.cursor.execute(
            """
            SELECT recursive_hash FROM recursion WHERE encoding_id = (?)
        """, (encoding_id, ))
        result = self.cursor.fetchall()
        return {r[0] for r in result}

    def clear_recursive_transformations_hashes(self, encoding_id: str):
        self.cursor.execute(
            """
            DELETE FROM recursion WHERE encoding_id = (?)
        """, (encoding_id, ))
        self.conn.commit()

    # # # # # # # #
    #  CLINGRAPH  #
    # # # # # # # #

    def save_clingraph(self, filename: str, encoding_id: str):
        self.cursor.execute(
            """
            INSERT OR REPLACE INTO clingraph (filename, encoding_id) VALUES (?, ?)
        """, (filename, encoding_id))
        self.conn.commit()

    def clear_clingraph(self, encoding_id: str):
        self.cursor.execute(
            """
            DELETE FROM clingraph WHERE encoding_id = (?)
        """, (encoding_id, ))
        self.conn.commit()

    def load_all_clingraphs(self, encoding_id: str) -> List[str]:
        self.cursor.execute(
            """
            SELECT filename FROM clingraph
            WHERE encoding_id = (?)
        """, (encoding_id, ))
        result = self.cursor.fetchall()
        return [r[0] for r in result]

    # # # # # # # #
    #   WARNINGS  #
    # # # # # # # #

    def clear_warnings(self, encoding_id: str):
        self.cursor.execute(
            """
            DELETE FROM warnings WHERE encoding_id = (?)
        """, (encoding_id, ))
        self.conn.commit()

    def save_warnings(self, warnings: List[TransformationError],
                      encoding_id: str):
        for warning in warnings:
            self.cursor.execute(
                """
                INSERT INTO warnings (encoding_id, warning) VALUES (?, ?)
            """, (encoding_id, current_app.json.dumps(warning)))
        self.conn.commit()

    def load_warnings(self, encoding_id: str) -> List[str]:
        self.cursor.execute(
            """
            SELECT warning FROM warnings WHERE encoding_id = (?)
        """, (encoding_id, ))
        result = self.cursor.fetchall()
        return [current_app.json.loads(r[0]) for r in result]

    # # # # # # # # # # # # # # #
    #   REGISTERED TRANFORMER   #
    # # # # # # # # # # # # # # #

    def save_transformer(self, transformer: TransformerTransport,
                         encoding_id: str):
        self.cursor.execute(
            """
            INSERT OR REPLACE INTO transformer (transformer, encoding_id) VALUES (?, ?)
        """, (current_app.json.dumps(transformer), encoding_id))
        self.conn.commit()

    def load_transformer(self, encoding_id: str) -> Optional[Transformer]:
        self.cursor.execute(
            """
            SELECT transformer FROM transformer WHERE encoding_id = (?)
        """, (encoding_id, ))
        result = self.cursor.fetchone()
        return current_app.json.loads(
            result[0]) if result is not None else None

    # # # # # # # #
    #   GENERAL   #
    # # # # # # # #

    def clear(self):
        self.cursor.execute("DELETE FROM encodings")
        self.cursor.execute("DELETE FROM models")
        self.cursor.execute("DELETE FROM graphs")
        self.cursor.execute("DELETE FROM current_graph")
        self.cursor.execute("DELETE FROM graph_relations")
        self.cursor.execute("DELETE FROM clingraph")
        self.cursor.execute("DELETE FROM transformer")
        self.cursor.execute("DELETE FROM warnings")
        self.conn.commit()


def get_database():
    if 'graph_accessor' not in g:
        g.graph_accessor = GraphAccessor()
    return g.graph_accessor


def load_program() -> str:
    encoding_id = get_or_create_encoding_id()
    return get_database().load_program(encoding_id)


def set_models(models: Sequence[Union[StableModel, str]]):
    encoding_id = get_or_create_encoding_id()
    get_database().set_models(models, encoding_id)


def load_models() -> List[StableModel]:
    encoding_id = get_or_create_encoding_id()
    return get_database().load_models(encoding_id)


def clear_models():
    encoding_id = get_or_create_encoding_id()
    get_database().clear_models(encoding_id)


def get_current_graph_hash() -> str:
    encoding_id = get_or_create_encoding_id()
    return get_database().get_current_graph_hash(encoding_id)

def save_sort(hash: str, sort: List[Transformation]):
    encoding_id = get_or_create_encoding_id()
    get_database().save_sort(hash, sort, encoding_id)

def save_many_sorts(sorts: List[Tuple[str, List[Transformation]]]) -> None:
    encoding_id = get_or_create_encoding_id()
    sorts_with_encoding_id = [(name, sort, encoding_id)
                              for name, sort in sorts]
    database = get_database()
    database.save_many_sorts(sorts_with_encoding_id)


def get_current_sort() -> List[Transformation]:
    encoding_id = get_or_create_encoding_id()
    return get_database().get_current_sort(encoding_id)

def get_all_sorts() -> List[str]:
    encoding_id = get_or_create_encoding_id()
    return get_database().load_all_sorts(encoding_id)

def insert_graph_relation(hash1: str, hash2: str, sort2: List[Transformation]):
    encoding_id = get_or_create_encoding_id()
    get_database().insert_graph_adjacency(hash1, hash2, sort2, encoding_id)

def get_adjacent_graphs_hashes(hash: str) -> List[str]:
    encoding_id = get_or_create_encoding_id()
    return get_database().get_adjacent_graphs_hashes(hash, encoding_id)

def save_dependency_graph(data: nx.DiGraph):
    encoding_id = get_or_create_encoding_id()
    get_database().save_dependency_graph(data, encoding_id)

def load_dependency_graph() -> nx.DiGraph:
    encoding_id = get_or_create_encoding_id()
    return get_database().load_dependency_graph(encoding_id)

def clear_all_sorts():
    encoding_id = get_or_create_encoding_id()
    get_database().clear_all_sorts(encoding_id)


def save_graph(data: nx.DiGraph, hash: str, sort: List[Transformation]):
    encoding_id = get_or_create_encoding_id()
    get_database().save_graph(data, hash, sort, encoding_id)


def get_graph() -> nx.DiGraph:
    encoding_id = get_or_create_encoding_id()
    graph = get_database().load_current_graph(encoding_id)
    return graph


def get_graph_json() -> str:
    encoding_id = get_or_create_encoding_id()
    return get_database().load_current_graph_json(encoding_id)


def set_current_graph(hash: str) -> str:
    encoding_id = get_or_create_encoding_id()
    db = get_database()
    if db.get_current_graph_hash(encoding_id) != hash:
        db.set_current_graph(hash, encoding_id)
    return get_graph_json()


def save_recursive_transformations_hashes(transformation_hashes: Set[str]):
    encoding_id = get_or_create_encoding_id()
    get_database().save_recursive_transformations_hashes(
        transformation_hashes, encoding_id)


def load_recursive_transformations_hashes() -> Set[str]:
    encoding_id = get_or_create_encoding_id()
    return get_database().load_recursive_transformations_hashes(encoding_id)


def save_clingraph(filename: str):
    database = get_database()
    encoding_id = get_or_create_encoding_id()
    database.save_clingraph(filename, encoding_id)


def clear_clingraph():
    database = get_database()
    encoding_id = get_or_create_encoding_id()
    database.clear_clingraph(encoding_id)


def load_clingraph_names():
    encoding_id = get_or_create_encoding_id()
    database = get_database()
    return database.load_all_clingraphs(encoding_id)


def load_transformer() -> Optional[Transformer]:
    encoding_id = get_or_create_encoding_id()
    return get_database().load_transformer(encoding_id)

def clear_graph():
    get_database().clear()


def save_transformer(transformer: TransformerTransport):
    encoding_id = get_or_create_encoding_id()
    get_database().save_transformer(transformer, encoding_id)

def save_warnings(warnings: List[TransformationError]):
    encoding_id = get_or_create_encoding_id()
    get_database().save_warnings(warnings, encoding_id)


def load_warnings() -> List[str]:
    encoding_id = get_or_create_encoding_id()
    return get_database().load_warnings(encoding_id)


def clear_warnings():
    encoding_id = get_or_create_encoding_id()
    get_database().clear_warnings(encoding_id)
