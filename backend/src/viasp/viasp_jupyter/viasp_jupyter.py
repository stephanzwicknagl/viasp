"""
    Create Environment and functions for running viASP in Jupyter Notebook.
    If executed in binder, proxies are considered.

    Functions:
        load(argv)
"""

import os

from jupyter_dash import JupyterDash
from jupyter_dash.comms import _jupyter_config
import viasp_dash
from viasp import Control
from viasp.server import startup
from .html import display_refresh_button

# if running in binder, get proxy information
# and set the backend URL, which will be used
# by the frontend
if 'BINDER_SERVICE_HOST' in os.environ:
    JupyterDash.infer_jupyter_proxy_config()
    display_refresh_button()
if ('server_url' in _jupyter_config and 'base_subpath' in _jupyter_config):
    _default_server_url = _jupyter_config['server_url']

    _default_requests_pathname_prefix = (
        _jupyter_config['base_subpath'].rstrip('/') + '/proxy/5050'
    )

    _VIASP_BACKEND_URL = _default_server_url+_default_requests_pathname_prefix
else:
    _VIASP_BACKEND_URL = "http://localhost:5050"

print(f"Starting backend at {_VIASP_BACKEND_URL}")


app = startup.run(mode="jupyter")
app.layout = viasp_dash.ViaspDash(
    id="myID",
    backendURL=_VIASP_BACKEND_URL
)

def load(argv):
    """
    An auxiliary function for quickly visualizing a program in Jupyter Notebook. Solves the program and marks all models for viasp.
    Usage: 
    ```python
        vj.load(['path/to/program.lp', ...])
        vj.app.run_server(mode='inline')
    ```
    """
    options = ["0"]

    ctl = Control(options, viasp_backend_url="http://localhost:5050")
    for path in argv:
        ctl.load(path)
    if not argv:
        ctl.load("-")
    ctl.ground([("base", [])])

    with ctl.solve(yield_=True) as handle:
        for m in handle:
            print(f"Answer:\n{m}")
            ctl.viasp.mark(m)
        print(handle.get())
    ctl.viasp.show()
