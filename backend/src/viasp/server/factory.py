from flask import Flask
from werkzeug.utils import find_modules, import_string

from flask_cors import CORS
from viasp.shared.io import DataclassJSONProvider
from ..shared.defaults import CLINGRAPH_PATH, GRAPH_PATH, PROGRAM_STORAGE_PATH, STDIN_TMP_STORAGE_PATH
import os, shutil, atexit


def register_blueprints(app):
    """collects all blueprints and adds them to the app object"""
    for name in find_modules('viasp.server.blueprints'):
        mod = import_string(name)
        if hasattr(mod, 'bp'):
            app.register_blueprint(mod.bp)
    return None


def create_app():
    app = Flask('api',static_url_path='/static', static_folder='/static')
    app.json = DataclassJSONProvider(app)
    app.config['CORS_HEADERS'] = 'Content-Type'

    register_blueprints(app)
    CORS(app, resources={r"/*": {"origins": "*"}}, max_age=3600)

    @atexit.register
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

    return app
