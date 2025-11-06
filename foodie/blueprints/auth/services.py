from werkzeug.security import check_password_hash

from foodie.db import db
from foodie.models import User


def authenticate_user(username: str, password: str) -> tuple[User | None, str | None]:
    """
    Authenticate a user with username and password.

    Args:
        username: Username
        password: Plain text password

    Returns:
        Tuple of (User instance if authenticated, error message if any)
    """
    user = db.session.query(User).filter_by(username=username).first()

    if user is None:
        return None, "Incorrect username."
    elif not check_password_hash(user.password, password):
        return None, "Incorrect password."

    return user, None
