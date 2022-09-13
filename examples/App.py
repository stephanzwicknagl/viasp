import sys
from clingo.application import clingo_main, Application
from clingo.script import enable_python
from viasp import Control2, startup

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
            unsat = handle.get().unsatisfiable
        ctl.viasp.show(unsat=unsat)

app = startup.run()

if __name__ == "__main__":
    clingo_main(App(), sys.argv[1:])
    app.run_server()
