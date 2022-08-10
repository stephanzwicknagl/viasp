import subprocess

import viasp_dash
from jupyter_dash import JupyterDash
from viasp import Control

from jupyter_dash.comms import _jupyter_config

JupyterDash.infer_jupyter_proxy_config()

if ('base_subpath' in _jupyter_config):
    _default_requests_pathname_prefix = (
        _jupyter_config['base_subpath'].rstrip('/') + '/proxy/5050'
    )

if ('server_url' in _jupyter_config):
    _default_server_url = _jupyter_config['server_url']


# if (_default_server_url in globals() and _default_requests_pathname_prefix in globals()):
    # _viasp_backend_url = _default_server_url+_default_requests_pathname_prefix
# else:
    # _viasp_backend_url = "http://localhost:5050"



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

subprocess.Popen(["viasp"])  # , stdout=subprocess.DEVNULL,
                #  stderr=subprocess.DEVNULL)
