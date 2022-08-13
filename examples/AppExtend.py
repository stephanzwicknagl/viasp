import sys
from clingo.application import Application, clingo_main

import viasp_dash
from dash import Dash
from viasp import Control


class ViaspApp(Application):
    program_name = "Viasp Integration"
    version = "1.0"

    def main(self, ctl, files):
        options = ["0"]

        outer_ctl = Control(options, control=ctl, viasp_backend_url="http://localhost:5050")

        for path in files: ctl.load(path)
        if not files:
            ctl.load("-")
        ctl.ground([("base",[])], context=self)

        for path in files: outer_ctl.load(path)
        if not files:
            outer_ctl.load("-")
        outer_ctl.ground([("base", [])])
        outer_ctl.solve()

        with ctl.solve(yield_=True) as handle:
            for m in handle:
                print("Answer:\n{}".format(m))
                outer_ctl.viasp.mark(m)
            # print(handle.get())

        outer_ctl.viasp.show()

app = Dash(__name__)

app.layout = viasp_dash.ViaspDash(
    id="myID",
    backendURL="http://localhost:5050"
)

if __name__ == "__main__":
    clingo_main(ViaspApp(), sys.argv[1:])
    app.run_server()
    print("done")
