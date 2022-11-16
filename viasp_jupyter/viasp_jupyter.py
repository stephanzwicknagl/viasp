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
from viasp import Control2
from viasp.server import startup
from IPython.display import HTML, display


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
    options = ["0"]

    ctl = Control2(options, viasp_backend_url="http://localhost:5050")
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

def initialize():
    display(HTML(
        '''
            <script>
                function restart_run_all(outp){
                    var output_area = outp.offsetParent.offsetParent;
                    console.log(output_area)
                    // find my cell element
                    var cell_element = output_area;
                    // which cell is it?
                    var cell_idx = Jupyter.notebook.get_cell_elements().index(cell_element);
                    console.log(cell_idx)
                    IPython.notebook.kernel.restart();
                    setTimeout(function(){
                        IPython.notebook.execute_cells([cell_idx]);
                    }, 10000)
                }
            </script>
            <button onclick="restart_run_all(this.parentNode.parentNode)">Click to Restart and Run</button>
        '''
    ))
