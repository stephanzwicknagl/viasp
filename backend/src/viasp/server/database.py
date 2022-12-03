from os.path import join, dirname, abspath
from typing import Optional, Set, List
from uuid import UUID

from ..shared.defaults import PROGRAM_STORAGE_PATH
from ..shared.event import Event, subscribe
from ..shared.model import ClingoMethodCall


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
            f.write(program)#.split("\n"))

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

    def get_pending(self) -> Optional[List[ClingoMethodCall]]:
        return list(filter(lambda call: call.uuid not in self.used, self.calls))

    def mark_call_as_used(self, call: ClingoMethodCall):
        self.used.add(call.uuid)
