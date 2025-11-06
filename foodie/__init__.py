import pathlib

import flask

from foodie.blueprints import admin, auth, home, order, restaurant
from foodie.db import db
from foodie.seed import init_seed_db_command


def create_app() -> flask.Flask:
    app = flask.Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=pathlib.Path(app.instance_path) / "foodie.sqlite",
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{app.instance_path}/foodie.sqlite",
    )
    pathlib.Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    # Initialize database
    db.init_app(app)
    with app.app_context():
        db.create_all()

    # Register database commands with flask cli
    init_seed_db_command(app)

    # Register routes
    app.register_blueprint(home.blueprint)
    app.register_blueprint(auth.blueprint)
    app.register_blueprint(restaurant.blueprint)
    app.register_blueprint(order.blueprint)
    app.register_blueprint(admin.blueprint)

    return app
