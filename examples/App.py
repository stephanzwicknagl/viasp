import sys
from clingo.application import clingo_main, Application
from clingo.script import enable_python
from viasp import Control2
from viasp.server import startup

enable_python()

class App(Application):

    def main(self, ctl, files):
        ctl = Control2(control=ctl, files=files)

        for path in files:
            ctl.load(path)
        if not files:
            ctl.load("-")
        ctl.ground([("base", [])])
        with ctl.solve(yield_=True) as handle:
            for m in handle:
                ctl.viasp.mark(m)
            print(handle.get())
            unsat=handle.get().unsatisfiable
        ctl.viasp.show()
        # ctl.viasp.clingraph(
        #     viz_encoding="clingraph/example5_viz.lp", #"clingraph/queens/viz.lp",#"
        #     engine="dot"
        # )


        if unsat:
            relaxed_prg = ctl.viasp.relax_constraints()
            print(relaxed_prg)
            ctl = Control2()
            ctl.add("base", [], relaxed_prg)
            ctl.ground([("base", [])])
            with ctl.solve(yield_ = True) as handle:
                for m in handle:
                    ctl.viasp.mark(m)
                print(handle.get())
            ctl.viasp.show()
        

app = startup.run()

if __name__ == "__main__":
    clingo_main(App(), sys.argv[1:])
    app.run()
