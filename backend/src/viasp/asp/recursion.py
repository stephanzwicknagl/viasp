from clingo import Number, Control


class RecursionReasoner:

    def __init__(self, **kwargs):
        self.atoms = []
        self.init = kwargs.pop("init", [])
        self.derivables = kwargs.pop("derivables", [])
        self.program = kwargs.pop("program", "")
        self.register_h_symbols = kwargs.pop("callback", None)
        self.conflict_free_h = kwargs.pop("conflict_free_h", "h")
        self.conflict_free_n = kwargs.pop("conflict_free_n", "n")

    def new(self):
        return self.atoms
    
    def derivable(self, atom):
        return Number(1) if atom in self.derivables else Number(0)

    def main(self):
        control = Control()
        control.add("iter", [f"{self.conflict_free_n}"], self.program)
        self.atoms = self.init

        step = 1
        while self.atoms != []:
            control.ground([("iter", [Number(step)])], context=self)
            self.atoms = [ x.symbol.arguments[1] for x in
                            control.symbolic_atoms.by_signature(self.conflict_free_h, 3)
                           if x.is_fact and x.symbol.arguments[0].number == step
                         ]
            step += 1

        for x in control.symbolic_atoms.by_signature(self.conflict_free_h, 3):
            self.register_h_symbols(x.symbol)
