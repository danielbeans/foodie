"""
Seed the database with initial data using SQLAlchemy models.
Run with: uv run flask --app foodie seed-db
"""

import click
from werkzeug.security import generate_password_hash

import flask

from foodie.db import db
from foodie.models import User


def seed_db():
    """Seed the database with initial data."""

    app = flask.current_app

    with app.app_context():
        create_users()


def create_users():
    # Default password for all test users
    default_password = generate_password_hash("password123")

    users = [
        User(
            username="nick-fury",
            password=default_password,
            full_name="Nick Fury",
            role="ADMIN",
            country="America",
        ),
        User(
            username="captain-marvel",
            password=default_password,
            full_name="Captain Marvel",
            role="MANAGER",
            country="India",
        ),
        User(
            username="captain-america",
            password=default_password,
            full_name="Captain America",
            role="MANAGER",
            country="America",
        ),
        User(
            username="thanos",
            password=default_password,
            full_name="Thanos",
            role="MEMBER",
            country="India",
        ),
        User(
            username="thor",
            password=default_password,
            full_name="Thor",
            role="MEMBER",
            country="India",
        ),
        User(
            username="travis",
            password=default_password,
            full_name="Travis",
            role="MEMBER",
            country="America",
        ),
    ]

    db.session.add_all(users)
    db.session.commit()


@click.command("seed-db")
def seed_db_command():
    seed_db()
    click.echo("Database seeded successfully.")


def init_seed_db_command(app):
    """Register the seed command with the Flask app."""

    app.cli.add_command(seed_db_command)
