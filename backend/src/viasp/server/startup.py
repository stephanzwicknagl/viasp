"""
    The module can be imported to create the dash app,
    set the standard layout and start the backend.

    The backend is killed automatically on keyboard interruptions.

    Make sure to import it as the first viasp module,
    before other modules (which are dependent on the backend).

    The backend is started on the localhost on port 5050.
"""
import sys
import os
import atexit
import shutil
from subprocess import Popen
import json
from retrying import retry

import viasp_dash
from dash import Dash, jupyter_dash
from dash._jupyter import _jupyter_config

from viasp import clingoApiClient
from viasp.shared.defaults import (DEFAULT_BACKEND_HOST, DEFAULT_BACKEND_PORT,
                                   DEFAULT_BACKEND_PROTOCOL, CLINGRAPH_PATH,
                                   GRAPH_PATH, PROGRAM_STORAGE_PATH,
                                   STDIN_TMP_STORAGE_PATH, COLOR_PALETTE_PATH)



def run(host=DEFAULT_BACKEND_HOST, port=DEFAULT_BACKEND_PORT):
    """ create the dash app, set layout and start the backend on host:port """

    # if running in binder, get proxy information
    # and set the backend URL, which will be used
    # by the frontend
    if 'BINDER_SERVICE_HOST' in os.environ:
        jupyter_dash.infer_jupyter_proxy_config()
    if ('server_url' in _jupyter_config and 'base_subpath' in _jupyter_config):
        _default_server_url = _jupyter_config['server_url']

        _default_requests_pathname_prefix = (
            _jupyter_config['base_subpath'].rstrip('/') + '/proxy/' +
            str(port))

        backend_url = _default_server_url + _default_requests_pathname_prefix
    elif 'google.colab' in sys.modules:
        from google.colab.output import eval_js  # type: ignore
        backend_url = eval_js(f"google.colab.kernel.proxyPort({port})")
    else:
        backend_url = f"{DEFAULT_BACKEND_PROTOCOL}://{host}:{port}"

    env = os.getenv("ENV", "production")
    if env == "production":
        command = ["waitress-serve", "--host", host, "--port", str(port), "--call", "viasp.server.factory:create_app"]
    else: 
        command = ["viasp_server", "--host", host, "--port", str(port)]
    # if 'ipykernel_launcher.py' in sys.argv[0]:
    #     display_refresh_button()

    print(f"Starting backend at {backend_url}")
    log = open('viasp.log', 'w', encoding="utf-8")
    viasp_backend = Popen(command, stdout=log, stderr=log)

    color_palette = json.load(open(COLOR_PALETTE_PATH, "r"))
    app = Dash(__name__)
    app.layout = viasp_dash.ViaspDash(id="myID",
                                      backendURL=backend_url,
                                      colorPalette=color_palette)
    app.title = "viASP"

    # suppress dash's flask server banner
    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None  # type: ignore

    # make sure the backend is up, before continuing with other modules
    @retry(
        stop_max_attempt_number=30,
        wait_exponential_multiplier=10,
        wait_exponential_max=10000,
    )
    def wait_for_backend():
        try:
            assert clingoApiClient.backend_is_running(backend_url)
        except Exception as e:
            raise Exception("Backend did not start in time.") from e

    try:
        wait_for_backend()
    except Exception as final_error:
        print(f"Error: {final_error}")
        viasp_backend.terminate()
        raise final_error

    def terminate_process(process):
        """ kill the backend on keyboard interruptions"""
        print("\nKilling Backend")
        try:
            process.terminate()
        except OSError:
            print("Could not terminate viasp")

    def close_file(file):
        """ close the log file"""
        file.close()

    def shutdown():
        """ when quitting app, remove all files in 
                the static/clingraph folder
                and auxiliary program files
        """
        if os.path.exists(CLINGRAPH_PATH):
            shutil.rmtree(CLINGRAPH_PATH)
        for file in [GRAPH_PATH, PROGRAM_STORAGE_PATH, STDIN_TMP_STORAGE_PATH]:
            if os.path.exists(file):
                os.remove(file)

    # kill the backend on keyboard interruptions
    atexit.register(terminate_process, viasp_backend)
    atexit.register(close_file, log)
    atexit.register(shutdown)

    return app
