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

# Start the backend
viaspBackend = Popen(["viasp"], stdout=None, stderr=None)
# make sure the backend is up, before continuing with other modules
while True:
    if clingoApiClient.backend_is_running():
        break

def terminate_process(process):
    """ kill the backend on keyboard interruptions"""
    print("Killing Backend")
    try:
        process.terminate()
    except OSError:
        print("Could not terminate viasp")

# kill the backend on keyboard interruptions
atexit.register(terminate_process, viaspBackend)
