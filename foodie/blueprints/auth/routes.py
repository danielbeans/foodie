import flask

from foodie.blueprints.auth.services import authenticate_user
from foodie.blueprints.auth.utils import load_logged_in_user

blueprint = flask.Blueprint("auth", __name__, url_prefix="/auth")
blueprint.before_app_request(load_logged_in_user)


@blueprint.route("/login", methods=("GET", "POST"))
def login() -> flask.Response:
    if flask.request.method == "POST":
        username = flask.request.form["username"]
        password = flask.request.form["password"]

        user, error = authenticate_user(username, password)

        if error:
            flask.flash(error, "danger")
            return flask.render_template("auth/login.html")

        flask.session.clear()
        flask.session["user_id"] = user.id
        flask.flash(f"Welcome back, {user.full_name}!", "success")
        return flask.redirect(flask.url_for("home.index"))

    return flask.render_template("auth/login.html")


@blueprint.route("/logout")
def logout() -> flask.Response:
    flask.session.clear()
    flask.flash("You have been logged out.", "info")
    return flask.redirect(flask.url_for("home.index"))
