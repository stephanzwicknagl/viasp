import argparse
import textwrap
import webbrowser
import importlib.metadata

from viasp import Control
from viasp.server import startup
from viasp.shared.defaults import DEFAULT_BACKEND_HOST, DEFAULT_BACKEND_PORT, DEFAULT_FRONTEND_PORT, DEFAULT_BACKEND_PROTOCOL

try:
    VERSION = importlib.metadata.version("viasp")
except importlib.metadata.PackageNotFoundError:
    VERSION = '0.0.0'

def _get_parser():
    parser = argparse.ArgumentParser(prog='viasp', description=textwrap.dedent(r"""
           _           _____ _____  
          (_)   /\    / ____|  __ \ 
    __   ___   /  \  | (___ | |__) |
    \ \ / / | / /\ \  \___ \|  ___/ 
     \ V /| |/ ____ \ ____) | |     
      \_/ |_/_/    \_\_____/|_|     
                    
    viASP is a package to generate interactive 
    visualizations of ASP programs and 
    their stable models. 
    """), formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('paths', nargs='+', help='Runs viASP with the paths to programs to be loaded')
    parser.add_argument('-n', '--models', type=int, help='Compute at most <n> models (0 for all)', default=0)
    parser.add_argument('--host', type=str, help='The host for the backend and frontend', default=DEFAULT_BACKEND_HOST)
    parser.add_argument('-p', '--port', type=int, help='The port for the backend', default=DEFAULT_BACKEND_PORT)
    parser.add_argument('-f', '--frontend-port', type=int, help='The port for the frontend', default=DEFAULT_FRONTEND_PORT)
    parser.add_argument('--version','-v', action='version',
                    version=f'%(prog)s {VERSION}')
    

    clingraph_group = parser.add_argument_group('Clingraph', 'If included, a clingraph visualization will be made.')
    clingraph_group.add_argument('--viz_encoding', type=str, help='The path to the visualization encoding.', default=None)
    clingraph_group.add_argument('--engine', type=str, help='The visualization engine.', default="dot")
    clingraph_group.add_argument('--graphviz_type', type=str, help='The graph type.', default="graph")

    relaxer_group = parser.add_argument_group('Relaxer', 'Options for the relaxation of integrity constraints in unsatisfiable programs.')
    relaxer_group.add_argument('-r', '--no-relaxer', action=argparse.BooleanOptionalAction, help='Do not use the relaxer')
    relaxer_group.add_argument('--head_name', type=str, help='The name of the head predicate.', default="unsat")
    relaxer_group.add_argument('--no-collect-variables', action=argparse.BooleanOptionalAction, help='Do not collect variables from body as a tuple in the head literal.')

    # TODO: transformer

    return parser


def backend():
    from viasp.server.factory import create_app
    parser = argparse.ArgumentParser(description='viasp backend')
    parser.add_argument('--host', type=str, help='The host for the backend', default=DEFAULT_BACKEND_HOST)
    parser.add_argument('-p', '--port', type=int, help='The port for the backend', default=DEFAULT_BACKEND_PORT)
    app = create_app()
    use_reloader = False
    debug = False
    args = parser.parse_args()
    host = args.host
    port = args.port
    print(f"Starting viASP backend at {host}:{port}")
    app.run(host=host, port=port, use_reloader=use_reloader, debug=debug)



def start():
    parser = _get_parser()

    args = parser.parse_args()
    models = args.models
    no_relaxer = args.no_relaxer
    paths = args.paths
    host = args.host
    port = args.port
    frontend_port = args.frontend_port
    viz_encoding = args.viz_encoding
    engine = args.engine
    graphviz_type = args.graphviz_type
    head_name = args.head_name
    no_collect_variables = args.no_collect_variables

    app = startup.run(host=DEFAULT_BACKEND_HOST, port=DEFAULT_BACKEND_PORT)
    
    options = [str(models)]

    backend_url = f"{DEFAULT_BACKEND_PROTOCOL}://{host}:{port}"
    ctl = Control(options, viasp_backend_url=backend_url)
    for path in paths:
        ctl.load(path)
    if len(paths) == 0:
        ctl.load("-")
    ctl.ground([("base", [])])

    with ctl.solve(yield_=True) as handle:
        for m in handle:
            print("Answer:\n{}".format(m))
            ctl.viasp.mark(m)
        print(handle.get())
        if handle.get().unsatisfiable and not no_relaxer:
            ctl = ctl.viasp.relax_constraints(head_name=head_name, collect_variables=not no_collect_variables)
    ctl.viasp.show()
    if viz_encoding:
        ctl.viasp.clingraph(viz_encoding=viz_encoding, engine=engine, graphviz_type=graphviz_type)

    webbrowser.open(f"http://{host}:{frontend_port}")
    app.run(host=host, port=frontend_port, use_reloader=False, debug=False)
