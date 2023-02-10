from .wrapper import ShowConnector
from .shared.defaults import STDIN_TMP_STORAGE_PATH
from inspect import signature
from clingo import Control as InnerControl

connector = None

def _get_connector(**kwargs):
    global connector
    if connector is None:
        connector = ShowConnector(**kwargs)
    return connector


def load_program_file(path: str, **kwargs) -> None:
    r"""
    Load a (non-ground) program file into the viasp backend

    :param path: ``str``
        path to the program file
    :param kwargs: 
        * *viasp_backend_url* (``str``) -- 
          url of the viasp backend
    
    """
    connector = _get_connector(**kwargs)
    connector.register_function_call(
        "__init__", signature(InnerControl.__init__), [], kwargs={})
    connector.register_function_call("load", signature(
        InnerControl.load), [], kwargs={"path": path})


def load_program_string(program: str, **kwargs) -> None:
    r"""
    Load a (non-ground) program into the viasp backend

    :param path: ``str``
        the program to load
    :param kwargs: 
        * *viasp_backend_url* (``str``) -- 
          url of the viasp backend
    """
    connector = _get_connector(**kwargs)
    with open(STDIN_TMP_STORAGE_PATH, "w", encoding="utf-8") as f:
        f.write(program)
    ctl = InnerControl
    connector.register_function_call(
        "__init__", signature(InnerControl.__init__), [], kwargs={})
    connector.register_function_call("load", signature(
        ctl.load), [], kwargs={"path": STDIN_TMP_STORAGE_PATH})


def _get_program_string(path):
    prg = ""
    with open(path, encoding="utf-8") as f:
        prg = "".join(f.readlines())
    return prg


def add_program_file(*args, **kwargs):
    r"""
    Add a (non-ground) program file to the viasp backend.
    This function provides two overloads, similar to ``clingo.control.Control.add``.
    
    ```python
    def add(self, name: str, parameters: Sequence[str], program: str) -> None:
        ...

    def add(self, program: str) -> None:
        return self.add("base", [], program)
    ```

    :param name: ``str``
        The name of program block to add.
    :param parameters: ``Sequence[str]``
        The parameters of the program block to add.
    :param program: ``str``
        The path to the non-ground program.
    :param kwargs: 
        * *viasp_backend_url* (``str``) -- 
            url of the viasp backend
    
    See Also
    --------
    add_program_string
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
    Add a (non-ground) program file to the viasp backend.
    This function provides two overloads, similar to ``clingo.control.Control.add``.
    
    ```python
    def add(self, name: str, parameters: Sequence[str], program: str) -> None:
        ...

    def add(self, program: str) -> None:
        return self.add("base", [], program)
    ```

    :param name: ``str``
        The name of program block to add.
    :param parameters: ``Sequence[str]``
        The parameters of the program block to add.
    :param program: ``str``
        The non-ground program in string form.
    :param kwargs: 
        * *viasp_backend_url* (``str``) -- 
            url of the viasp backend

    See also:
    ---------
    add_program_file
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


def show() -> None:
    """
    Generate the graph from the loaded program and the marked models.
    """
    connector = _get_connector()
    connector.show()

def unmark(model) -> None:
    """
    Unmark a model.
    
    :param model: ``int``
        The model to unmark.
    """
    connector = _get_connector()
    connector.unmark(model)

def mark(model) -> None:
    connector = _get_connector()
    connector.mark(model)

def clear() -> None:
    """
    Clear all marked models.
    """
    connector = _get_connector()
    connector.clear()

def relax_constraints(*args, **kwargs) -> str:
    connector = _get_connector()
    return connector.relax_constraints(*args, **kwargs)

def clingraph(viz_encoding, engine) -> None:
    connector = _get_connector()
    connector.clingrpah(viz_encoding,engine)