import pathlib

import flask

from foodie.blueprints import home

from . import db


def create_app():
    app = flask.Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=pathlib.Path(app.instance_path) / "foodie.sqlite",
    )
    # app.config.from_pyfile("config.py")
    pathlib.Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    # Register click command with flask cli
    db.init_app(app)

    # Register routes
    app.register_blueprint(home.blueprint)

    return app
