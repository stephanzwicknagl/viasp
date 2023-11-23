from clingo import Control
from viasp.asp.justify import save_model
from clingo.ast import parse_string, AST, Transformer as ClingoTransformer


def traveling_salesperson():
    return """
start(a).
city(a). city(b). city(c). city(d).
road(a,b,10). road(b,c,20). road(c,d,25). road(d,a,40). road(b,d,30). road(d,c,25). road(c,a,35).
road(c,b, 25). road(b,c,25). road(a,c,10).


{ travel(X,Y) } :- road(X,Y,_).
visited(Y) :- travel(X,Y), start(X). visited(Y) :- travel(X,Y), visited(X).
:- city(X), not visited(X).
:- city(X), 2 { travel(X,Y) }. :- city(X), 2 { travel(Y,X) }.

#minimize { D,X,Y : travel(X,Y), road(X,Y,D) }.
"""


def traveling_salesperson_without_minimize():
    return "\n".join(traveling_salesperson().split("\n")[:-1])


def traveling_salesperson_without_minimize_and_constraints():
    return "\n".join(traveling_salesperson_without_minimize().split("\n")[:-3])

def get_stable_models_for_program(program):
    saved_models = []
    ctl = Control(["0"])
    ctl.add("base", [], program)
    ctl.ground([("base", [])])
    with ctl.solve(yield_=True) as handle: # type: ignore
        for model in handle:
            saved_models.append(save_model(model))
    return saved_models

def parse_program_to_ast(prg: str) -> AST:
    program_base = "#program base."
    parsed = []
    parse_string(prg, lambda rule: parsed.append(rule))
    if str(parsed[0]) == program_base:
        return parsed[1]
    return parsed[0]

class Transformer(ClingoTransformer):
    def __init__(self):
        super().__init__()

    def visit_Rule(self, rule):
        return 