from sqlalchemy.orm import DeclarativeBase
import flask_sqlalchemy


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


db = flask_sqlalchemy.SQLAlchemy(model_class=Base)
