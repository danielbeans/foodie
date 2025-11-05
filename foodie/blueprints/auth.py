import flask

blueprint = flask.Blueprint("auth", __name__, url_prefix="/auth")


@blueprint.route("/login", methods=("GET", "POST"))
def login():
    return flask.render_template("auth/login.html")
