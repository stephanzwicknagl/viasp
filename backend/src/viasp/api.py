"""
This module can be used to interact with the viasp backend.

It provides similar functions to viASP's proxy Control class,
but works independently of a clingo Control object program.

In addition to the proxy's functions, this module provides functions to
interact with it outside of a clingo program. Models can be marked
directly from strings or files containing the corresponding facts.
"""

from inspect import signature
from typing import List, cast, Union
import webbrowser

import clingo
from clingo import Control as InnerControl
from clingo import Model as clingo_Model
from clingo import ast
from clingo.ast import AST, ASTSequence, ASTType, Transformer
from clingo.symbol import Symbol
from clingo.script import enable_python

from .shared.defaults import DEFAULT_BACKEND_HOST, DEFAULT_BACKEND_PORT, DEFAULT_FRONTEND_PORT, STDIN_TMP_STORAGE_PATH, DEFAULT_BACKEND_PROTOCOL
from .shared.io import clingo_symbols_to_stable_model, clingo_model_to_stable_model
from .shared.model import StableModel
from .wrapper import ShowConnector, Control as viaspControl
from .exceptions import InvalidSyntax
from .server import startup

__all__ = [
    "viasp",
    "load_program_file",
    "load_program_string",
    "add_program_file",
    "add_program_string",
    "mark_from_clingo_model",
    "mark_from_string",
    "mark_from_file",
    "unmark_from_clingo_model",
    "unmark_from_string",
    "unmark_from_file",
    "clear",
    "show",
    "get_relaxed_program",
    "relax_constraints",
    "clingraph",
    "register_transformer",
]

SHOWCONNECTOR = None

def _get_connector(**kwargs):
    global SHOWCONNECTOR
    if SHOWCONNECTOR is None:
        SHOWCONNECTOR = ShowConnector(**kwargs)
        SHOWCONNECTOR.register_function_call(
            "__init__", signature(InnerControl.__init__), [], kwargs={})
    return SHOWCONNECTOR


def _get_program_string(path: Union[str, List[str]]) -> str:
    prg = ""
    if isinstance(path, str):
        path = [path]
    for p in path:
        with open(p, encoding="utf-8") as f:
            prg += "".join(f.readlines())
    return prg


def _is_running_in_notebook():
    try:
        shell = get_ipython().__class__.__name__  # type: ignore
        if shell == 'ZMQInteractiveShell':
            return True  # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False  # Probably standard Python interpreter


def viasp(**kwargs) -> None:
    r"""
    Single endpoint to start a viasp visualization. 
    This function loads the input program, solves it, and visualizes the models.
    Optional settings for the visualization can be provided.

    :param \**kwargs: 
        * *models* (``int``) --
            number of models to compute, defaults to `0` (compute all)
        * *paths* (``list``) --
            list of paths to program files
        * *opt_mode* (``tuple``) --
            optimization mode and bounds for clingo optimization. Tuple must contain one of {opt|enum|optN|ignore} in the first element and a list of strings in the second element. Defaults to `('opt', [])`
        * *viz_encoding* (``str``) --
            path to the clingraph visualization encoding
        * *engine* (``str``) --
            clingraph visualization engine, defaults to "dot"
        * *graphviz_type* (``str``) --
            clingraph graph type, default "graph"
        * *no_relaxer* (``bool``) --
            do not relax constraints of unsatisfiable programs, defaults to `False`
        * *head_name* (``str``) --
            name of head literal in relaxed program, defaults to "unsat"
        * *no_collect_variables* (``bool``) --
            do not collect variables from body in relaxed program, defaults to `False`
        * *host* (``str``) --
            host of the backend, defaults to `localhost`
        * *port* (``int``) --
            port of the backend, defaults to `5050`
        * *frontend_port* (``int``) --
            port of the frontend, defaults to `8050`
    """
    models = kwargs.get("models", 0)
    no_relaxer = kwargs.get("no_relaxer", False)
    paths = kwargs.get("paths", [])
    host = kwargs.get("host", DEFAULT_BACKEND_HOST)
    port = kwargs.get("port", DEFAULT_BACKEND_PORT)
    frontend_port = kwargs.get("frontend_port", DEFAULT_FRONTEND_PORT)
    viz_encoding = kwargs.get("viz_encoding", None)
    engine = kwargs.get("engine", "dot")
    graphviz_type = kwargs.get("graphviz_type", "graph")
    head_name = kwargs.get("head_name", "unsat")
    no_collect_variables = kwargs.get("no_collect_variables", False)
    opt_mode, bounds = kwargs.get("opt_mode") or ('opt', [])
    opt_mode_str = f"--opt-mode={opt_mode}" + (f",{','.join(bounds)}"
                                               if len(bounds) > 0 else "")

    app = startup.run(host=DEFAULT_BACKEND_HOST, port=DEFAULT_BACKEND_PORT)

    options = [str(models), opt_mode_str]

    backend_url = f"{DEFAULT_BACKEND_PROTOCOL}://{host}:{port}"
    enable_python()
    ctl = viaspControl(options, viasp_backend_url=backend_url)
    for path in paths:
        ctl.load(path)
    if len(paths) == 0:
        ctl.load("-")
    ctl.ground([("base", [])])

    with ctl.solve(yield_=True) as handle:
        models = {}
        for m in handle:
            print(f"Answer: {m.number}\n{m}")
            if len(m.cost) > 0:
                print(f"Optimization: {m.cost}")
            c = m.cost[0] if len(m.cost) > 0 else 0
            models[clingo_model_to_stable_model(m)] = c
        for m in list(
                filter(lambda i: models.get(i) == min(models.values()),
                       models.keys())):
            ctl.viasp.mark(m)
        print(handle.get())
        if handle.get().unsatisfiable and not no_relaxer:
            ctl = ctl.viasp.relax_constraints(
                head_name=head_name,
                collect_variables=not no_collect_variables)
    ctl.viasp.show()
    if viz_encoding:
        ctl.viasp.clingraph(viz_encoding=viz_encoding,
                            engine=engine,
                            graphviz_type=graphviz_type)

    if not _is_running_in_notebook():
        webbrowser.open(f"http://{host}:{frontend_port}")
    app.run(host=host,
            port=frontend_port,
            use_reloader=False,
            debug=False,
            dev_tools_silence_routes_logging=True)


def load_program_file(path: Union[str, List[str]], **kwargs) -> None:
    r"""
    Load a (non-ground) program file into the viasp backend

    :param path: ``str`` or ``list``
        path or list of paths to the program file
    :param \**kwargs: 
        * *viasp_backend_url* (``str``) --
          url of the viasp backend
        * *_viasp_client* (``ClingoClient``) --
          a viasp client object
    
    See Also
    --------
    ``load_program_string``
    """
    connector = _get_connector(**kwargs)
    if isinstance(path, str):
        path = [path]
    for p in path:
        connector.register_function_call("load", signature(
            InnerControl.load), [], kwargs={"path": p})


def load_program_string(program: str, **kwargs) -> None:
    r"""
    Load a (non-ground) program into the viasp backend

    :param program: ``str``
        the program to load
    :param \**kwargs:
        * *viasp_backend_url* (``str``) --
          url of the viasp backend
        * *_viasp_client* (``ClingoClient``) --
          a viasp client object
    
    See Also
    --------
    ``load_program_file``
    """
    connector = _get_connector(**kwargs)
    with open(STDIN_TMP_STORAGE_PATH, "w", encoding="utf-8") as f:
        f.write(program)
    connector.register_function_call("load", signature(
        InnerControl.load), [], kwargs={"path": STDIN_TMP_STORAGE_PATH})



def add_program_file(*args, **kwargs):
    r"""
    Add a (non-ground) program file to the viasp backend.
    This function provides two overloads, similar to ``clingo.control.Control.add``.

    .. code-block:: python

        def add(self, name: str, parameters: Sequence[str], path: str) -> None:
            ...

        def add(self, path: str) -> None:
            return self.add("base", [], path)

    :param name: ``str``
        The name of program block to add.
    :param parameters: ``Sequence[str]``
        The parameters of the program block to add.
    :param path: ``str`` or ``list``
        The path or list of paths to the non-ground program.
    :param \**kwargs:
        * *viasp_backend_url* (``str``) -- 
          url of the viasp backend
        * *_viasp_client* (``ClingoClient``) -- 
          a viasp client object

    See Also
    --------
    ``add_program_string`` 
    """
    if "_viasp_client" in kwargs:
        del kwargs["_viasp_client"]

    n = len(args) + len(kwargs)
    if n == 1:
        kwargs["program"] = _get_program_string(args[0])
        args = []
    elif "program" in kwargs:
        kwargs["program"]= _get_program_string(kwargs["program"])
    else:
        kwargs["program"] = _get_program_string(args[2])

    add_program_string(*args,**kwargs)


def add_program_string(*args, **kwargs) -> None:
    r"""
    Add a (non-ground) program to the viasp backend.
    This function provides two overloads, similar to ``clingo.control.Control.add``.

    .. code-block:: python
        
        def add(self, name: str, parameters: Sequence[str], program: str) -> None:
            ...
        
        def add(self, program: str) -> None:
            return self.add("base", [], program)

    :param name: ``str``
        The name of program block to add.
    :param parameters: ``Sequence[str]``
        The parameters of the program block to add.
    :param program: ``str``
        The non-ground program in string form.
    :param \**kwargs:
        * *viasp_backend_url* (``str``) --
          url of the viasp backend
        * *_viasp_client* (``ClingoClient``) --
          a viasp client object

    See also
    ---------
    ``add_program_file``
    """
    connector = _get_connector(**kwargs)
    if "_viasp_client" in kwargs:
        del kwargs["_viasp_client"]


    n = len(args) + len(kwargs)
    if n == 1:
        pass_kwargs = dict(zip(['name', 'parameters', 'program'], \
                               ["base", [], kwargs["program"] \
                                    if "program" in kwargs else args[0]]))
    else:
        pass_kwargs = dict()
        pass_kwargs["name"] = kwargs["name"] \
                    if "name" in kwargs else args[0]
        pass_kwargs["parameters"] = kwargs["parameters"] \
                    if "parameters" in kwargs else args[1]
        pass_kwargs["program"] = kwargs["program"] \
                    if "program" in kwargs else args[2]

    connector.register_function_call(
        "add", signature(InnerControl._add2), [], kwargs=pass_kwargs)


def show(**kwargs) -> None:
    r"""
    Propagate the marked models to the backend and Generate the graph.
    
    :param \**kwargs: 
        * *viasp_backend_url* (``str``) --
          url of the viasp backend
        * *_viasp_client* (``ClingoClient``) --
          a viasp client object

    """
    connector = _get_connector(**kwargs)
    connector.show()


def mark_from_clingo_model(model: Union[clingo_Model, StableModel], **kwargs) -> None:
    r"""
    Mark a model to be visualized. Models can be unmarked and cleared.
    The marked models are propagated to the backend when ``show`` is called.

    :param model: ``clingo.solving.Model`` or ``viasp.model.StableModel``
        The model to mark.
    :param \**kwargs:
        * *viasp_backend_url* (``str``) --
          url of the viasp backend
        * *_viasp_client* (``ClingoClient``) --
          a viasp client object

    See Also
    --------
    ``unmark_from_clingo_model``
    ``mark_from_string``
    ``mark_from_file``
    """
    connector = _get_connector(**kwargs)
    connector.mark(model)


def unmark_from_clingo_model(model: Union[clingo_Model, StableModel],
                             **kwargs) -> None:
    r"""
    Unmark a model.

    :param model: ``clingo.solving.Model`` or ``viasp.model.StableModel``
        The model to unmark.
    :param \**kwargs:
        * *viasp_backend_url* (``str``) --
          url of the viasp backend
        * *_viasp_client* (``ClingoClient``) --
          a viasp client object
    
    See Also
    --------
    ``mark_from_clingo_model``
    ``unmark_from_string``
    ``unmark_from_file``
    """
    connector = _get_connector(**kwargs)
    connector.unmark(model)


def clear(**kwargs) -> None:
    r"""
    Clear all marked models.

    :param \**kwargs: 
        * *viasp_backend_url* (``str``) --
          url of the viasp backend
        * *_viasp_client* (``ClingoClient``) --
          a viasp client object

    """
    connector = _get_connector(**kwargs)
    connector.clear()


def get_relaxed_program(*args, **kwargs) -> Union[str, None]:
    r"""
    Relax constraints in the marked models. Returns
    the relaxed program as a string.

    :param head_name: (``str``, optional) Name of head literal, defaults to "unsat"
    :param collect_variables: (``bool``, optional) Collect variables from body as a tuple in the head literal, defaults to True
    :param \**kwargs:
        * *viasp_backend_url* (``str``) --
          url of the viasp backend
        * *_viasp_client* (``ClingoClient``) --
          a viasp client object
    
    See also
    --------
    ``relax_constraints``
    """
    head_name = kwargs.pop("head_name", "unsat")
    collect_variables = kwargs.pop("collect_variables", True)
    connector = _get_connector(**kwargs)
    return connector.get_relaxed_program(head_name, collect_variables)

def relax_constraints(*args, **kwargs) -> viaspControl:
    r"""
    Relax constraints in the marked models. Returns 
    a new viaspControl object with the relaxed program loaded
    and stable models marked.

    :param head_name: (``str``, optional) Name of head literal. Defaults to "unsat"
    :param collect_variables: (``bool``, optional) Collect variables from body as a tuple in the head literal. Defaults to True
    :param \**kwargs:
        * *viasp_backend_url* (``str``) --
          url of the viasp backend
        * *_viasp_client* (``ClingoClient``) --
          a viasp client object

    See also
    --------
    ``get_relaxed_program``
    """
    head_name = kwargs.pop("head_name", "unsat")
    collect_variables = kwargs.pop("collect_variables", True)
    connector = _get_connector(**kwargs)
    return connector.relax_constraints(head_name, collect_variables)

def clingraph(viz_encoding, engine="dot", graphviz_type="graph", **kwargs) -> None:
    r"""
    Generate the a clingraph from the marked models and the visualization encoding.

    :param viz_encoding: ``str``
        The path to the visualization encoding.
    :param engine: ``str``
        The visualization engine. Defaults to "dot".
    :param graphviz_type: ``str``
        The graph type. Defaults to "graph".
    :param kwargs:
        * *viasp_backend_url* (``str``) --
          url of the viasp backend
        * *_viasp_client* (``ClingoClient``) --
          a viasp client object
    
    Note
    --------
    See https://github.com/potassco/clingraph for more details.
    """
    connector = _get_connector(**kwargs)
    connector.clingraph(viz_encoding, engine, graphviz_type)

def register_transformer(transformer: Transformer, imports: str = "", path: str = "", **kwargs) -> None:
    r"""
    Register a transformer to the backend. The program will be transformed
    in the backend before further processing is made.

    :param transformer: ``Transformer``
        The transformer to register.
    :param imports: ``str``
        The imports usued by the transformer.
        (Can only be clingo imports and standard imports. 
        String lines must be separated by newlines.)
    :param path: ``str``
        The path to the transformer.
    :param kwargs:
        * *viasp_backend_url* (``str``) --
          url of the viasp backend
        * *_viasp_client* (``ClingoClient``) --
          a viasp client object
    """
    connector = _get_connector(**kwargs)
    connector.register_transformer(transformer, imports, path)

# ------------------------------------------------------------------------------
# Parse ASP facts from a string or files into a clingo model
# ------------------------------------------------------------------------------


class ClingoParserWrapperError(Exception):
    r"""A special exception for returning from the clingo parser.

    I think the clingo parser is assuming all exceptions behave as if they have
    a copy constructor.

    """
    def __init__(self, arg):
        if type(arg) == type(self):
            self.exc = arg.exc
        else:
            self.exc = arg
        super().__init__()


class FactParserError(Exception):
    def __init__(self,message: str, line: int, column: int):
        self.line = line
        self.column = column
        super().__init__(message)


class NonFactVisitor:
    ERROR_AST = set({
        ASTType.Id,
        ASTType.Variable,
        ASTType.BinaryOperation,
        ASTType.Interval,
        ASTType.Pool,
        ASTType.BooleanConstant,
        ASTType.Comparison,
        getattr(ASTType, "Guard" if isinstance(clingo.version(), tuple) and clingo.version() >= (5, 6, 0)
                         else "AggregateGuard"),
        ASTType.ConditionalLiteral,
        ASTType.Aggregate,
        ASTType.BodyAggregateElement,
        ASTType.BodyAggregate,
        ASTType.HeadAggregateElement,
        ASTType.HeadAggregate,
        ASTType.Disjunction,
        ASTType.TheorySequence,
        ASTType.TheoryFunction,
        ASTType.TheoryUnparsedTermElement,
        ASTType.TheoryUnparsedTerm,
        ASTType.TheoryGuard,
        ASTType.TheoryAtomElement,
        ASTType.TheoryAtom,
        ASTType.TheoryOperatorDefinition,
        ASTType.TheoryTermDefinition,
        ASTType.TheoryGuardDefinition,
        ASTType.TheoryAtomDefinition,
        ASTType.Definition,
        ASTType.ShowSignature,
        ASTType.ShowTerm,
        ASTType.Minimize,
        ASTType.Script,
        ASTType.External,
        ASTType.Edge,
        ASTType.Heuristic,
        ASTType.ProjectAtom,
        ASTType.ProjectSignature,
        ASTType.Defined,
        ASTType.TheoryDefinition})

    def __call__(self, stmt: AST) -> None:
        self._stmt = stmt
        self._visit(stmt)

    def _visit(self, ast_in: AST) -> None:
        '''
        Dispatch to a visit method.
        '''
        if (ast_in.ast_type in NonFactVisitor.ERROR_AST or
                (ast_in.ast_type == ASTType.Function and ast_in.external)):
            line = cast(ast.Location, ast_in.location).begin.line
            column = cast(ast.Location, ast_in.location).begin.column
            exc = FactParserError(message=f"Non-fact '{self._stmt}'",
                                  line=line, column=column)
            raise ClingoParserWrapperError(exc)

        for key in ast_in.child_keys:
            subast = getattr(ast_in, key)
            if isinstance(subast, ASTSequence):
                for x in subast:
                    self._visit(x)
            if isinstance(subast, AST):
                self._visit(subast)


def parse_fact_string(aspstr: str, raise_nonfact: bool = False) -> List[Symbol]:
    ctl = InnerControl()
    try:
        if raise_nonfact:
            with ast.ProgramBuilder(ctl) as bld:
                nfv = NonFactVisitor()

                def on_rule(ast: AST) -> None:
                    nonlocal nfv, bld
                    if nfv: nfv(ast)
                    bld.add(ast)
                ast.parse_string(aspstr, on_rule)
        else:
            ctl.add("base", [], aspstr)
    except ClingoParserWrapperError as e:
        raise e.exc

    ctl.ground([("base", [])])

    return [sa.symbol for sa in ctl.symbolic_atoms if sa.is_fact]


def mark_from_string(model: str, **kwargs) -> None:
    r"""
    Parse a string of ASP facts and mark them as a model.

    Facts must be of a simple form. Rules that are NOT simple facts include: any
    rule with a body, a disjunctive fact, a choice rule, a theory atom, a literal
    with an external @-function reference, a literal that requires some mathematical
    calculation (eg., "p(1+1).")

    Models can be unmarked and cleared.
    The marked models are propagated to the backend when ``show`` is called.

    :param model: ``str``
        The facts of the model to mark.
    :param \**kwargs:
        * *viasp_backend_url* (``str``) --
          url of the viasp backend
        * *_viasp_client* (``ClingoClient``) --
          a viasp client object
        
    :raises: :py:class:`InvalidSyntax` if the string contains non-facts.

    See Also
    --------
    ``mark_from_clingo_model``
    ``mark_from_file``
    ``unmark_from_string``
    """
    try:
        symbols = parse_fact_string(model, raise_nonfact=True)
        connector = _get_connector(**kwargs)
        stable_model = clingo_symbols_to_stable_model(symbols)
        connector.mark(stable_model)
    except RuntimeError as e:
        msg = "Syntactic error the input string can't be read as facts. \n"
        raise InvalidSyntax(msg,str(e)) from None


def mark_from_file(path: Union[str, List[str]], **kwargs) -> None:
    r"""
    Parse a file containing a string of ASP facts and mark them as a model.

    Facts must be of a simple form. Rules that are NOT simple facts include: any
    rule with a body, a disjunctive fact, a choice rule, a theory atom, a literal
    with an external @-function reference, a literal that requires some mathematical
    calculation (eg., "p(1+1).")

    Models can be unmarked and cleared.
    The marked models are propagated to the backend when ``show`` is called.

    :param path: ``str`` or ``list``
        The path or list of paths to the file containing the facts of the model to mark.
    :param \**kwargs:
        * *viasp_backend_url* (``str``) --
          url of the viasp backend
        * *_viasp_client* (``ClingoClient``) --
          a viasp client object
    
    :raises: :py:class:`InvalidSyntax` if the string contains non-facts.

    See Also
    --------
    ``mark_from_clingo_model``
    ``mark_from_string``
    ``unmark_from_file``
    """
    mark_from_string(_get_program_string(path), **kwargs)


def unmark_from_string(model: str, **kwargs) -> None:
    r"""
    Parse a string of ASP facts and unmark the corresponding model.

    The string must be an exact match to the model.

    Facts must be of a simple form. Rules that are NOT simple facts include: any
    rule with a body, a disjunctive fact, a choice rule, a theory atom, a literal
    with an external @-function reference, a literal that requires some mathematical
    calculation (eg., "p(1+1).").

    Changes to marked models are propagated to the backend when ``show`` is called.

    :param model: ``str``
        The facts of the model to unmark.
    :param \**kwargs:
        * *viasp_backend_url* (``str``) --
          url of the viasp backend
        * *_viasp_client* (``ClingoClient``) --
          a viasp client object

    :raises: :py:class:`InvalidSyntax` if the string contains non-facts.

    See Also
    --------
    ``unmark_from_clingo_model``
    ``unmark_from_file``
    """
    try:
        symbols = parse_fact_string(model, raise_nonfact=True)
        connector = _get_connector(**kwargs)
        stable_model = clingo_symbols_to_stable_model(symbols)
        connector.unmark(stable_model)
    except RuntimeError as e:
        msg = "Syntactic error the input string can't be read as facts. \n"
        raise InvalidSyntax(msg,str(e)) from None


def unmark_from_file(path: str, **kwargs) -> None:
    r"""
    Parse a file containing a string of ASP facts and unmark the corresponding model.

    The string must be an exact match to the model.

    Facts must be of a simple form. Rules that are NOT simple facts include: any
    rule with a body, a disjunctive fact, a choice rule, a theory atom, a literal
    with an external @-function reference, a literal that requires some mathematical
    calculation (eg., "p(1+1).").

    Changes to marked models are propagated to the backend when ``show`` is called.

    :param path: ``str``
        The path to the file containing the facts of the model to unmark.
    :param \**kwargs:
        * *viasp_backend_url* (``str``) --
          url of the viasp backend
        * *_viasp_client* (``ClingoClient``) --
          a viasp client object
    
    :raises: :py:class:`InvalidSyntax` if the string contains non-facts.

    See Also
    --------
    ``unmark_from_clingo_model``
    ``unmark_from_string``
    """
    unmark_from_string(_get_program_string(path), **kwargs)
