import sys

import viasp_dash
from dash import Dash
from viasp import Control, start_backend


def main():
    options = ["0"]

    ctl = Control(options, viasp_backend_url="http://localhost:5050")
    for path in sys.argv[1:]:
        ctl.load(path)
    if not sys.argv[1:]:
        ctl.load("-")
    ctl.ground([("base", [])])

    with ctl.solve(yield_=True) as handle:
        for m in handle:
            print("Answer:\n{}".format(m))
            ctl.viasp.mark(m)
        print(handle.get())
    ctl.viasp.show()


start_backend.run()
app = Dash(__name__)

app.layout = viasp_dash.ViaspDash(
    id="myID",
    backendURL="http://localhost:5050"
)

if __name__ == '__main__':
    main()
    app.run_server()
