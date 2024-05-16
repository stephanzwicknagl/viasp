import argparse
from asyncio import constants
import cmd
import textwrap
import sys
import re
import os
import webbrowser
import subprocess

import importlib.metadata
from typing import Union, Tuple
from clingo.script import enable_python

import clingraph
from viasp import Control as viaspControl, viasp
from viasp.server import startup
from viasp.shared.defaults import DEFAULT_BACKEND_HOST, DEFAULT_BACKEND_PORT, DEFAULT_FRONTEND_PORT, DEFAULT_BACKEND_PROTOCOL
from viasp.shared.io import clingo_model_to_stable_model

try:
    VERSION = importlib.metadata.version("viasp")
except importlib.metadata.PackageNotFoundError:
    VERSION = '0.0.0'


def _parse_opt_mode(arg):
    parts = arg.split(',')
    mode = parts[0]
    if mode not in ['opt', 'enum', 'optN', 'ignore']:
        raise argparse.ArgumentTypeError(f"Invalid opt-mode: {mode}")
    bounds = parts[1:]
    return (mode, bounds)


def _get_parser():
    parser = argparse.ArgumentParser(
        prog='viasp',
        description=textwrap.dedent(r"""
           _        _____ _____  
          (_)  /\  / ____|  __ \ 
    __   ___  /  \| (___ | |__) |
    \ \ / / |/ /\ \\___ \|  ___/ 
     \ V /| / ____ \___) | |     
      \_/ |/_/    \_\___/|_|     
                    
    viASP is a package to generate interactive 
    visualizations of ASP programs and 
    their stable models. 
    """),
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        'paths',
        nargs='+',
        help='Runs viASP with the paths to programs to be loaded')
    parser.add_argument('-n',
                        '--models',
                        type=int,
                        help='Compute at most <n> models (0 for all)',
                        default=0)
    parser.add_argument('--host',
                        type=str,
                        help='The host for the backend and frontend',
                        default=DEFAULT_BACKEND_HOST)
    parser.add_argument('-p',
                        '--port',
                        type=int,
                        help='The port for the backend',
                        default=DEFAULT_BACKEND_PORT)
    parser.add_argument('-f',
                        '--frontend-port',
                        type=int,
                        help='The port for the frontend',
                        default=DEFAULT_FRONTEND_PORT)
    parser.add_argument('--version',
                        '-v',
                        action='version',
                        version=f'%(prog)s {VERSION}')
    parser.add_argument('--opt-mode',
                        type=_parse_opt_mode,
                        help=textwrap.dedent("""
    Configure optimization algorithm
    <mode {opt|enum|optN|ignore}>[,<bound>...]
    opt   : Find optimal model
    enum  : Enumerate models with costs less than or equal to some fixed bound
    optN  : Find optimum, then enumerate optimal models
    ignore: Ignore optimize statements
    """))

    clingraph_group = parser.add_argument_group(
        'Clingraph', 'If included, a clingraph visualization will be made.')
    clingraph_group.add_argument(
        '--viz_encoding',
        type=str,
        help='The path to the visualization encoding.',
        default=None)
    clingraph_group.add_argument('--engine',
        type=str,
        help='The visualization engine.',
        default="dot")
    clingraph_group.add_argument('--graphviz_type',
        type=str,
        help='The graph type.',
        default="graph")

    relaxer_group = parser.add_argument_group(
        'Relaxer',
        'Options for the relaxation of integrity constraints in unsatisfiable programs.')
    relaxer_group.add_argument('-r',
                               '--no-relaxer',
                               action=argparse.BooleanOptionalAction,
                               help='Do not use the relaxer')
    relaxer_group.add_argument('--head_name',
                               type=str,
                               help='The name of the head predicate.',
                               default="unsat")
    relaxer_group.add_argument(
        '--no-collect-variables',
        action=argparse.BooleanOptionalAction,
        help=
        'Do not collect variables from body as a tuple in the head literal.')

    # TODO: transformer

    return parser


def backend():
    from viasp.server.factory import create_app
    parser = argparse.ArgumentParser(description='viasp backend')
    parser.add_argument('--host',
                        type=str,
                        help='The host for the backend',
                        default=DEFAULT_BACKEND_HOST)
    parser.add_argument('-p',
                        '--port',
                        type=int,
                        help='The port for the backend',
                        default=DEFAULT_BACKEND_PORT)
    app = create_app()
    use_reloader = False
    debug = False
    args = parser.parse_args()
    host = args.host
    port = args.port
    print(f"Starting viASP backend at {host}:{port}")
    app.run(host=host, port=port, use_reloader=use_reloader, debug=debug)


def start():
    # parser = _get_parser()
    # args = parser.parse_args()
    # viasp(**vars(args))
    main()

def main():
    Viasp().run(sys.argv[1:])


#
# MyArgumentParser
#


class MyArgumentParser(argparse.ArgumentParser):

    def print_help(self, file=None):
        if file is None:
            file = sys.stdout
        file.write("viasp version {}\n".format(VERSION))
        argparse.ArgumentParser.print_help(self, file)

    def error(self, message):
        raise argparse.ArgumentError(None, "In context <viasp>: " + message)


class SmartFormatter(argparse.RawDescriptionHelpFormatter):

    def _split_lines(self, text, width):
        if text.startswith('R|'):
            return text[2:].splitlines()
        return argparse.RawDescriptionHelpFormatter._split_lines(
            self, text, width)


#
# class viaspArgumentParser
#
class ViaspArgumentParser:

    clingo_help = """
Clingo Options:
  --<option>[=<value>]\t: Set clingo <option> [to <value>]

    """

    usage = "viasp [number] [options] [files]"

    epilog = """
Default command-line:
viasp --models 0 [files]

viasp is part of Potassco: https://potassco.org/
Get help/report bugs via : https://potassco.org/support
    """

    version_string = "viasp " + VERSION + """
Copyright (C) Stephan Zwicknagl, Luis Glaser
License: The MIT License <https://opensource.org/licenses/MIT>"""

    def __init__(self):
        self.underscores = 0
        self.__first_file: str = ""
        self.__file_warnings = []

    def __update_underscores(self, new):
        i = 0
        while len(new) > i and new[i] == "_":
            i += 1
        if i > self.underscores: self.underscores = i

    def __add_file(self, files, file):
        abs_file = os.path.abspath(file) if file != "-" else "-"
        if abs_file in [i[1] for i in files]:
            self.__file_warnings.append(file)
        else:
            files.append((file, abs_file))
        if not self.__first_file:
            self.__first_file = file

    def __do_constants(self, alist):
        try:
            constants = dict()
            for i in alist:
                old, sep, new = i.partition("=")
                self.__update_underscores(new)
                if new == "":
                    raise Exception(
                        "no definition for constant {}".format(old))
                if old in constants:
                    raise Exception("constant {} defined twice".format(old))
                else:
                    constants[old] = new
            return constants
        except Exception as e:
            self.__cmd_parser.error(str(e))

    def __do_opt_mode(self, opt_mode):
        try:
            parts = opt_mode.split(',')
            mode = parts[0]
            if mode not in ['opt', 'enum', 'optN', 'ignore']:
                raise argparse.ArgumentTypeError(f"Invalid opt-mode: {mode}")
            bounds = parts[1:]
            return (mode, bounds)
        except Exception as e:
            self.__cmd_parser.error(str(e))

    def run(self, args):

        # command parser
        _epilog = self.clingo_help + "\nusage: " + self.usage + self.epilog
        cmd_parser = MyArgumentParser(
            usage=self.usage,
            epilog=_epilog,
            formatter_class=
            SmartFormatter,  #argparse.RawDescriptionHelpFormatter,
            add_help=False,
            prog="viasp")
        self.__cmd_parser = cmd_parser

        # Basic Options
        basic = cmd_parser.add_argument_group('Basic Options')
        basic.add_argument('--help',
            '-h',
            action='help',
            help=': Print help and exit')
        basic.add_argument('--clingo-help',
            help=HELP_CLINGO_HELP,
            type=int,
            dest='clingo_help',
            metavar='<m>',
            default=0,
            choices=[0, 1, 2, 3])
        basic.add_argument('--version',
            '-v',
            dest='version',
            action='store_true',
            help=': Print version information and exit')
        #basic.add_argument('--minimize', dest='minimize',
        #                   help=argparse.SUPPRESS,
        #                   action='store_true')

        # Solving Options
        solving = cmd_parser.add_argument_group('Solving Options')
        solving.add_argument('-c',
            '--const',
            dest='constants',
            action="append",
            help=argparse.SUPPRESS,
            default=[])
        solving.add_argument('--const-nb',
            dest='constants_nb',
            action="append",
            metavar="<id>=<t>",
            help=HELP_CONST_NONBASE,
            default=[])
        solving.add_argument('--opt-mode',
            type=self.__do_opt_mode,
            help=HELP_OPT_MODE)
        solving.add_argument('--models',
            '-n',
            help=": Compute at most <n> models (0 for all)",
            type=int,
            dest='max_models',
            metavar='<n>',
            default=1)
        solving.add_argument('--project',
            dest='project',
            help=HELP_PROJECT,
            action='store_true')

        viasp_options = cmd_parser.add_argument_group('viasp Options')
        viasp_options.add_argument('--host',
            type=str,
            help=': The host for the backend and frontend',
            default=DEFAULT_BACKEND_HOST)
        viasp_options.add_argument('-p',
            '--port',
            type=int,
            help=': The port for the backend',
            default=DEFAULT_BACKEND_PORT)
        viasp_options.add_argument('-f',
            '--frontend-port',
            type=int,
            help=': The port for the frontend',
            default=DEFAULT_FRONTEND_PORT)

        clingraph_group = cmd_parser.add_argument_group(
            'Clingraph', 'If included, a clingraph visualization will be made.')
        clingraph_group.add_argument(
            '--viz-encoding',
            type=str,
            help=': The path to the visualization encoding.',
            default=None)
        clingraph_group.add_argument('--engine',
            type=str,
            help=': The visualization engine.',
            default="dot")
        clingraph_group.add_argument('--graphviz-type',
            type=str,
            help=': The graph type.',
            default="graph")

        relaxer_group = cmd_parser.add_argument_group(
            'Relaxer',
            'Options for the relaxation of integrity constraints in unsatisfiable programs.'
        )
        relaxer_group.add_argument('-r',
            '--no-relaxer',
            action=argparse.BooleanOptionalAction,
            help=': Do not use the relaxer')
        relaxer_group.add_argument('--head-name',
            type=str,
            help=': The name of the head predicate.',
            default="unsat")
        relaxer_group.add_argument(
            '--no-collect-variables',
            action=argparse.BooleanOptionalAction,
            help=
            ': Do not collect variables from body as a tuple in the head literal.')



        options, unknown = cmd_parser.parse_known_args(args=args)
        options = vars(options)

        # print version
        if options['version']:
            print(self.version_string)
            sys.exit(0)

        # separate files, number of models and clingo options
        options['files'], clingo_options = [], []
        for i in unknown:
            if i == "-":
                self.__add_file(options['files'], i)
            elif (re.match(r'^([0-9]|[1-9][0-9]+)$', i)):
                options['max_models'] = int(i)
            elif (re.match(r'^-', i)):
                clingo_options.append(i)
            else:
                self.__add_file(options['files'], i)

        # when no files, add stdin
        # build prologue
        if options['files'] == []:
            self.__first_file = "stdin"
            options['files'].append(("-", "-"))
        if len(options['files']) > 1:
            self.__first_file = f"{self.__first_file} ..."
        prologue = "viasp version " + VERSION + "\nReading from " + self.__first_file + "\n"

        # handle constants
        options['constants'] = self.__do_constants(options['constants'])
        options['constants_nb'] = self.__do_constants(options['constants_nb'])
        # clingo_options['constants'] = options['constants']
        # clingo_options['constants_nb'] = options['constants_nb']

        # handle clingraph
        options['clingraph_files'] = []
        if options['viz_encoding']:
            self.__add_file(options['clingraph_files'], options.pop('viz_encoding'))

        # return
        return options, clingo_options, self.underscores, prologue, \
               self.__file_warnings



class Viasp():

    def run(self, args):
        vap = ViaspArgumentParser()
        options, clingo_options, underscores, prologue, file_warnings = vap.run(args)

        if options['clingo_help'] > 0:
            subprocess.Popen(["clingo", "--help=" + str(options['clingo_help'])]).wait()
            sys.exit(0)

        print(prologue)

        # print(F"options: {options}")
        # print(F"clingo_options: {clingo_options}")
        # print(F"underscores: {underscores}")
        # print(F"prologue: {prologue}")
        # print(F"file_warnings: {file_warnings}")

        constants = options.get('constants', {})
        constants_nb = options.get('constants_nb', {})
        opt_mode, bounds = options.get("opt_mode") or ('opt', [])
        opt_mode_str = f"--opt-mode={opt_mode}" + (f",{','.join(bounds)}"
            if len(bounds) > 0 else "")
        no_relaxer = options.get("no_relaxer", False)
        host = options.get("host", DEFAULT_BACKEND_HOST)
        port = options.get("port", DEFAULT_BACKEND_PORT)
        frontend_port = options.get("frontend_port", DEFAULT_FRONTEND_PORT)

        viz_encoding = options.get("viz_encoding", None)
        engine = options.get("engine", "dot")
        graphviz_type = options.get("graphviz_type", "graph")
        head_name = options.get("head_name", "unsat")
        no_collect_variables = options.get("no_collect_variables", False)
        paths = options.get("files", [])

        app = startup.run(host=DEFAULT_BACKEND_HOST, port=DEFAULT_BACKEND_PORT)

        ctl_options = ['--models', str(options['max_models']), opt_mode_str]
        for k,v in constants.items():
            ctl_options.extend(["--const", f"{k}={v}"])
        for k,v in constants_nb.items():
            ctl_options.extend(["--constants-nb", f"{k}={v}"])
        backend_url = f"{DEFAULT_BACKEND_PROTOCOL}://{host}:{port}"
        enable_python()
        ctl = viaspControl(ctl_options, viasp_backend_url=backend_url)
        for path in paths:
            ctl.load(path[-1])
        if len(paths) == 0:
            ctl.load("-")
        ctl.ground([("base", [])])

        with ctl.solve(yield_=True) as handle:
            models = {}
            for m in handle:
                print(f"Answer: {m.number}\n{m}")
                if len(m.cost) > 0:
                    print(f"Optimization: {m.cost}")
                c = m.cost[0] if len(m.cost) > 0 else 0
                models[clingo_model_to_stable_model(m)] = c
            for m in list(
                    filter(lambda i: models.get(i) == min(models.values()),
                        models.keys())):
                ctl.viasp.mark(m)
            print(handle.get())
            if handle.get().unsatisfiable and not no_relaxer:
                ctl = ctl.viasp.relax_constraints(
                    head_name=head_name,
                    collect_variables=not no_collect_variables)
        ctl.viasp.show()
        if viz_encoding:
            ctl.viasp.clingraph(viz_encoding=viz_encoding,
                                engine=engine,
                                graphviz_type=graphviz_type)

        if not _is_running_in_notebook():
            webbrowser.open(f"http://{host}:{frontend_port}")
        app.run(host=host,
                port=frontend_port,
                use_reloader=False,
                debug=False,
                dev_tools_silence_routes_logging=True)




def _is_running_in_notebook():
    try:
        shell = get_ipython().__class__.__name__  # type: ignore
        if shell == 'ZMQInteractiveShell':
            return True  # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False  # Probably standard Python interpreter

#
# DEFINES
#

#
UNKNOWN = "UNKNOWN"
ERROR = "*** ERROR: (asprin): {}"
ERROR_INFO = "*** Info : (asprin): Try '--help' for usage information"
ERROR_OPEN = "<cmd>: error: file could not be opened:\n  {}\n"
ERROR_FATAL = "Fatal error, this should not happen.\n"
ERROR_PARSING = "parsing failed"
#ERROR_IMPROVE_1 = "options --stats and --improve-limit cannot be used together"
ERROR_IMPROVE_2 = """incorrect value for option --improve-limit, \
options reprint and nocheck cannot be used together"""
DEBUG = "--debug"
TEST = "--test"
ALL_CONFIGS = ["tweety", "trendy", "frumpy", "crafty", "jumpy", "handy"]
HELP_PROJECT = """R|: Enable projective solution enumeration,
  projecting on the formulas of the specification"""
HELP_HEURISTIC = """R|: Apply domain heuristics with value <v> and modifier <m>
  on formulas of the preference specification"""
HELP_ON_OPT_HEURISTIC = """R|: Apply domain heuristics depending on the last optimal model
  <t> has the form [+|-],[s|p],<v>,<m> and applies value <v> and modifier <m>
  to the atoms that are either true (+) or false (-) in the last optimal model 
  and that either are shown (s) or appear in the preference specification (p)"""
HELP_DELETE_BETTER = """R|: After computing an optimal model,
  add a program to delete models better than that one"""
HELP_TOTAL_ORDER = """R|: Do not add programs for optimal models after the \
first one
  Use only if the preference specification represents a total order"""
HELP_GROUND_ONCE = """R|: Ground preference program only once \
(for improving a model)"""
HELP_CLINGO_HELP = ": Print {1=basic|2=more|3=full} clingo help and exit"
HELP_RELEASE_LAST = """R|: Improving a model, release the preference program \
for the last model
  as soon as possible"""
HELP_NO_OPT_IMPROVING = """R|: Improving a model, do not use optimal models"""
HELP_VOLATILE_IMPROVING = """R|: Use volatile preference programs \
for improving a model"""
HELP_VOLATILE_OPTIMAL = """R|: Use volatile preference programs \
for optimal models"""
HELP_TRANS_EXT = """R|: Configure handling of extended rules \
for non base programs
  (<m> should be as in clingo --trans-ext option)"""
HELP_CONST_NONBASE = """R|: Replace term occurrences of <id> in non-base
  programs with <t>"""
# quick projects and is complete, but does not reprint the unknown models
# at the end, while nocheck projects and never checks if the unknown models are
# optimal,  hence it is not complete
HELP_CONFIGS = """R|: Run clingo configurations c1, ..., cn iteratively
  (use 'all' for running all configurations)"""
HELP_NO_META = """R|: Do not use meta-programming solving methods
  Note: This may be incorrect for computing many models when the preference program
        is not stratified"""
HELP_META = """R|: Apply or disable meta-programming solving methods, where <m> can be:
  * simple: translate to a disjunctive logic program
  * query: compute optimal models that contain atom 'query' using simple
  * combine: combine normal iterative asprin mode (to improve a model)
             with simple (to check that a model is not worse than previous optimal models)
  * no: disable explicitly meta-programming solving methods
        this may be incorrect for computing many models using nonstratified preference programs
  Add ',bin' to use a clingo binary for reification
  Add ',sat' to use a clingo binary and systems lp2normal2 and lp2sat for reification"""

HELP_OPT_MODE = """R|: Configure optimization algorithm
  <mode {opt|enum|optN|ignore}>[,<bound>...]
  opt   : Find optimal model
  enum  : Enumerate models with costs less than or equal to some fixed bound
  optN  : Find optimum, then enumerate optimal models
  ignore: Ignore optimize statements"""

#
# VERSION
#
