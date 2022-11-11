"""
    Create Environment and functions for running viASP in Jupyter Notebook.
    If executed in binder, proxies are considered.

    Functions:
        load(argv)
"""

import os

from jupyter_dash import JupyterDash
from jupyter_dash.comms import _jupyter_config
from viasp import Control
from viasp.server import startup


# if running in binder, get proxy information
# and set the backend URL, which will be used
# by the frontend
if 'BINDER_SERVICE_HOST' in os.environ:
    try:
        JupyterDash.infer_jupyter_proxy_config()
    except EnvironmentError:
        pass
if ('server_url' in _jupyter_config and 'base_subpath' in _jupyter_config):
    _default_server_url = _jupyter_config['server_url']

    _default_requests_pathname_prefix = (
        _jupyter_config['base_subpath'].rstrip('/') + '/proxy/5050'
    )

    _viasp_backend_url = _default_server_url+_default_requests_pathname_prefix
else:
    _viasp_backend_url = "http://localhost:5050"

print(f"Starting backend at {_viasp_backend_url}")

app = startup.run(mode="jupyter", proxy_url=_viasp_backend_url)

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
