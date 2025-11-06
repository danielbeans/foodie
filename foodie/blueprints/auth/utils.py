import functools
from typing import Callable

import flask

from foodie.db import db
from foodie.models import User


def load_logged_in_user() -> None:
    """
    Load the logged-in user's information before each request.

    Requires flask app context.
    """
    user_id = flask.session.get("user_id")

    if user_id is None:
        flask.g.user = None
    else:
        flask.g.user = db.session.query(User).filter_by(id=user_id).first()


def login_required(view: Callable) -> Callable:
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


def role_required(*roles: str) -> Callable:
    """
    Decorator to require specific role(s) for a view.

    Args:
        roles: List of roles to require

    Usage: @role_required('ADMIN') or @role_required('ADMIN', 'MANAGER')
    """

    def decorator(view: Callable) -> Callable:
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            if flask.g.user is None:
                flask.flash("Please log in to access this page.", "warning")
                return flask.redirect(flask.url_for("auth.login"))

            if flask.g.user.role not in roles:
                flask.flash("You do not have permission to access this page.", "danger")
                return flask.redirect(flask.url_for("home.index"))

            return view(**kwargs)

        return wrapped_view

    return decorator


def check_country_access(country: str) -> bool:
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
