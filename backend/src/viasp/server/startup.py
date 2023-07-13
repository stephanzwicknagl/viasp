"""
    The module can be imported to create the dash app,
    set the standard layout and start the backend.

    The backend is killed automatically on keyboard interruptions.

    Make sure to import it as the first viasp module,
    before other modules (which are dependent on the backend).

    The backend is started on the localhost on port 5050.
"""

import atexit
from subprocess import Popen
from time import time
import viasp_dash
from dash import Dash

from viasp import clingoApiClient
from viasp.shared.defaults import (DEFAULT_BACKEND_HOST, DEFAULT_BACKEND_PORT,
                                   DEFAULT_BACKEND_PROTOCOL)


def run(mode="dash", host=DEFAULT_BACKEND_HOST, port=DEFAULT_BACKEND_PORT):
    """ create the dash app, set layout and start the backend on host:port """

    backend_url = f"{DEFAULT_BACKEND_PROTOCOL}://{host}:{port}"
    command = ["viasp", "--host", host, "--port", str(port)]

    app = Dash(__name__)
    if mode.lower() != "jupyter":
        app.layout = viasp_dash.ViaspDash(
            id="myID",
            backendURL=backend_url
            )

    log = open('viasp.log', 'a', encoding="utf-8")
    viasp_backend = Popen(command, stdout=log, stderr=log)

    # make sure the backend is up, before continuing with other modules
    t_start = time()
    while True:
        if clingoApiClient.backend_is_running(backend_url):
            break
        if time() - t_start > 30:
            raise Exception("Backend did not start in time.")

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

    # kill the backend on keyboard interruptions
    atexit.register(terminate_process, viasp_backend)
    atexit.register(close_file, log)

    return app
