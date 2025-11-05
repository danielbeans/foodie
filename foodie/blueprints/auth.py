import functools
import flask
from werkzeug.security import check_password_hash

from foodie.db import db
from foodie.models import User

blueprint = flask.Blueprint("auth", __name__, url_prefix="/auth")


@blueprint.route("/login", methods=("GET", "POST"))
def login():
    if flask.request.method == "POST":
        username = flask.request.form["username"]
        password = flask.request.form["password"]

        user = db.session.query(User).filter_by(username=username).first()

        if user is None:
            flask.flash("Incorrect username.", "danger")
            return flask.render_template("auth/login.html")
        elif not check_password_hash(user.password, password):
            flask.flash("Incorrect password.", "danger")
            return flask.render_template("auth/login.html")

        flask.session.clear()
        flask.session["user_id"] = user.id
        flask.flash(f"Welcome back, {user.full_name}!", "success")
        return flask.redirect(flask.url_for("home.index"))

    return flask.render_template("auth/login.html")


@blueprint.route("/logout")
def logout():
    flask.session.clear()
    flask.flash("You have been logged out.", "info")
    return flask.redirect(flask.url_for("home.index"))


@blueprint.before_app_request
def load_logged_in_user():
    """Load the logged-in user's information before each request."""
    user_id = flask.session.get("user_id")

    if user_id is None:
        flask.g.user = None
    else:
        flask.g.user = db.session.query(User).filter_by(id=user_id).first()


def login_required(view):
    """
    Decorator to require login for a view.

    Usage: @login_required
    """

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if flask.g.user is None:
            flask.flash("Please log in to access this page.", "warning")
            return flask.redirect(flask.url_for("auth.login"))
        return view(**kwargs)

    return wrapped_view


def check_country_access(country):
    """
    Check if the current user has access to data from the specified country.

    Requires flask app context.

    Args:
        country: The country to check access for

    Returns:
        True if user has access, False otherwise
    """
    if flask.g.user is None:
        return False

    if flask.g.user.role == "ADMIN":
        return True

    return flask.g.user.country == country
