import flask

blueprint = flask.Blueprint("home", __name__, template_folder="templates")


@blueprint.route("/")
def index() -> flask.Response:
    return flask.render_template("home.html")
