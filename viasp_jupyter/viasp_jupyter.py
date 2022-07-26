import subprocess

import viasp_dash
from jupyter_dash import JupyterDash
from viasp import Control


def load(argv):
    options = ["0"]

    ctl = Control(options, viasp_backend_url="http://localhost:5050")
    for path in argv:
        ctl.load(path)
    if not argv:
        ctl.load("-")
    ctl.ground([("base", [])])

    with ctl.solve(yield_=True) as handle:
        for m in handle:
            print("Answer:\n{}".format(m))
            ctl.viasp.mark(m)
        print(handle.get())
    ctl.viasp.show()


app = JupyterDash(__name__)

app.layout = viasp_dash.ViaspDash(
    id="myID",
    backendURL="http://localhost:5050"
)

subprocess.Popen(["viasp"],stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
