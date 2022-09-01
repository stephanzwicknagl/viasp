"""
    The module can be imported to start the backend and kill
    it automatically on keyboard interruptions.

    Make sure to import it as the first viasp module,
    before other modules (which are dependent on the backend).

    The backend is started on the localhost on port 5050.
"""

from subprocess import Popen
import atexit
from viasp import clingoApiClient
from viasp.shared.defaults import DEFAULT_BACKEND_HOST, DEFAULT_BACKEND_PORT, DEFAULT_BACKEND_PROTOCOL

def run(host=DEFAULT_BACKEND_HOST, port=DEFAULT_BACKEND_PORT):
    """ start the backend on host:port """

    backend_url = f"{DEFAULT_BACKEND_PROTOCOL}://{host}:{port}"
    command = ["viasp", "--host", host, "--port", str(port)]

    log = open('viasp.log', 'a', encoding="utf-8")
    viasp_backend = Popen(command, stdout=log, stderr=log)
    # make sure the backend is up, before continuing with other modules
    while True:
        if clingoApiClient.backend_is_running(backend_url):
            break

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
