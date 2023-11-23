import argparse

from viasp.shared.defaults import DEFAULT_BACKEND_HOST, DEFAULT_BACKEND_PORT


def start():
    from viasp.server.factory import create_app
    parser = argparse.ArgumentParser(description='viasp backend')
    parser.add_argument('--host', type=str, help='The host for the backend', default=DEFAULT_BACKEND_HOST)
    parser.add_argument('-p', '--port', type=int, help='The port for the backend', default=DEFAULT_BACKEND_PORT)
    app = create_app()
    use_reloader = False
    debug = True
    args = parser.parse_args()
    host = args.host
    port = args.port
    print(f"Starting viASP backend at {host}:{port}")
    app.run(host=host, port=port, use_reloader=use_reloader, debug=debug)
