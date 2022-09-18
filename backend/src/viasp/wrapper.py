import json
import sys
import shutil
import re
from inspect import signature
from typing import List

from clingo import Control as InnerControl, Model
from dataclasses import asdict, is_dataclass

from .clingoApiClient import ClingoClient
from .shared.defaults import STDIN_TMP_STORAGE_PATH, SHARED_PATH
from .shared.io import clingo_model_to_stable_model
from .shared.model import StableModel


def is_non_cython_function_call(attr: classmethod):
    return hasattr(attr, "__call__") and not attr.__name__.startswith("_") and not attr.__name__.startswith("<")

def transform_constraints(program):
    regex = r"(?<=\.)\s*:-|^\s*:-"
    
    matchNum = 1
    while re.search(regex, program) != None:
        program = re.sub(regex, f"unsat(r{matchNum}):-", program, 1)
        matchNum += 1

    program = program + ":~unsat(R).[1,R]"
    return program

class ShowConnector:

    def __init__(self, **kwargs):
        self._marked: List[StableModel] = []
        if "_viasp_client" in kwargs:
            self._database = kwargs["_viasp_client"]
        else:
            self._database = ClingoClient(**kwargs)
        self._connection = None

    def show(self, unsat=False):
        if not unsat:
            self._database.set_target_stable_model(self._marked)
            self._database.show()
        else:
            path = STDIN_TMP_STORAGE_PATH
            path_unsat = SHARED_PATH / "viasp_unsat_stdin_tmp.lp"
            with open(path) as f:
                program = ''.join(f.read().splitlines())
            transformed_constraints = transform_constraints(program)
            with open(path_unsat, "w", encoding="utf-8") as f:
                f.write(transformed_constraints)
            ctl_unsat = Control2()
            ctl_unsat.load(path_unsat)
            ctl_unsat.ground([("base", [])])
            with ctl_unsat.solve(yield_=True) as handle:
                for m in handle:
                    ctl_unsat.viasp.mark(m)
            ctl_unsat.viasp.show(unsat=False)

    def unmark(self, model: Model):
        serialized = clingo_model_to_stable_model(model)
        self._marked.remove(serialized)

    def mark(self, model: Model):
        serialized = clingo_model_to_stable_model(model)
        self._marked.append(serialized)

    def clear(self):
        self._marked.clear()

    def register_function_call(self, name, sig, args, kwargs):
        self._database.register_function_call(name, sig, args, kwargs)

    def relax_constraints(self):
        return self._database.relax_constraints()
        # return self._database.get_relaxed_program()



class Control(InnerControl):

    def __init__(self, *args, **kwargs):
        self.viasp = ShowConnector(**kwargs)
        if "_viasp_client" in kwargs:
            del kwargs["_viasp_client"]
        if "viasp_backend_url" in kwargs:
            del kwargs["viasp_backend_url"]
        self.viasp.register_function_call("__init__", signature(super().__init__), args, kwargs)
        super().__init__(*args, **kwargs)

    def load(self, path: str) -> None:
        if path == "-":
            path = STDIN_TMP_STORAGE_PATH
            tmp = sys.stdin.readlines()
            with open(path, "w", encoding="utf-8") as f:
                f.writelines(tmp)
        else:
            shutil.copy(path, STDIN_TMP_STORAGE_PATH)
            path = STDIN_TMP_STORAGE_PATH
        self.viasp.register_function_call("load", signature(self.load), [], kwargs={"path": path})
        super().load(path=str(path))

    def __getattribute__(self, name):
        attr = InnerControl.__getattribute__(self, name)
        if is_non_cython_function_call(attr) and name != "load":
            def wrapper_func(*args, **kwargs):
                self.viasp.register_function_call(attr.__name__, signature(attr), args, kwargs)
                result = attr(*args, **kwargs)
                return result

            return wrapper_func
        else:
            return attr


class Control2:
    
    
    def __init__(self, *args, **kwargs):
        if 'files' in kwargs:
            arguments = ([opt for opt in sys.argv[1:] if opt not in kwargs['files']])
            args = (arguments,)
            del kwargs['files']
        if 'control' in kwargs:
            self.passed_control = kwargs['control']
            del kwargs['control']
        else:
            self.passed_control = InnerControl(*args)
        self.viasp = ShowConnector(**kwargs)

        if "_viasp_client" in kwargs:
            del kwargs["_viasp_client"]
        if "viasp_backend_url" in kwargs:
            del kwargs["viasp_backend_url"]
        
        self.viasp.register_function_call("__init__", signature(self.passed_control.__init__), args, kwargs)

    def load(self, path: str) -> None:
        if path == "-":
            path = STDIN_TMP_STORAGE_PATH
            tmp = sys.stdin.readlines()
            with open(path, "w", encoding="utf-8") as f:
                f.writelines(tmp)
        else:
            shutil.copy(path, STDIN_TMP_STORAGE_PATH)
            path = STDIN_TMP_STORAGE_PATH
        self.viasp.register_function_call("load", signature(self.passed_control.load), [], kwargs={"path": path}) #? or self.passed_control.load
        self.passed_control.load(path=str(path))


    def __getattribute__(self, name):
        try:
            attr = object.__getattribute__(self, name)
        except AttributeError:
            attr = self.passed_control.__getattribute__(name) 
        if is_non_cython_function_call(attr) and name != "load":
            def wrapper_func(*args, **kwargs):
                self.viasp.register_function_call(attr.__name__, signature(attr), args, kwargs)
                result = attr(*args, **kwargs)
                return result

            return wrapper_func
        else:
            return attr

class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if is_dataclass(o):
            return asdict(o)
        return super().default(o)
