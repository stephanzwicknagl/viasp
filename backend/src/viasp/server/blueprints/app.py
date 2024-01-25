from flask import Blueprint

bp = Blueprint("app", __name__, template_folder='../templates', static_folder='../static/', static_url_path='/static')


@bp.route("/healthcheck", methods=["GET"])
def check_available():
    return "ok"
