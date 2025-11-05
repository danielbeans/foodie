"""
Seed the database with initial data using SQLAlchemy models.
Run with: uv run flask --app foodie seed-db
"""

import click
import json
import pathlib
from werkzeug.security import generate_password_hash

import flask

from foodie.db import db
from foodie.models import User, Restaurant, MenuItem


def load_seed_data():
    seed_file = pathlib.Path(__file__).parent.parent / "seed_data.json"
    with seed_file.open() as f:
        return json.load(f)


def seed_db():
    """Seed the database with initial data from JSON file."""

    app = flask.current_app

    with app.app_context():
        data = load_seed_data()
        create_users(data["users"])
        create_restaurants(data["restaurants"])


def create_users(users_data):
    """Create users from JSON data."""
    users = []
    for user_data in users_data:
        user = User(
            username=user_data["username"],
            password=generate_password_hash(user_data["password"]),
            full_name=user_data["full_name"],
            role=user_data["role"],
            country=user_data["country"],
        )
        users.append(user)

    db.session.add_all(users)
    db.session.commit()
    click.echo(f"Created {len(users)} users.")


def create_restaurants(restaurants_data):
    """Create restaurants and menu items from JSON data."""
    for restaurant_data in restaurants_data:
        restaurant = Restaurant(
            name=restaurant_data["name"],
            description=restaurant_data["description"],
            country=restaurant_data["country"],
            address=restaurant_data["address"],
            phone=restaurant_data["phone"],
        )
        db.session.add(restaurant)
        # Flush the session to get the restaurant ID before creating menu items
        db.session.flush()

        menu_items = []
        for item_data in restaurant_data.get("menu_items", []):
            menu_item = MenuItem(
                restaurant_id=restaurant.id,
                name=item_data["name"],
                description=item_data["description"],
                price=item_data["price"],
            )
            menu_items.append(menu_item)

        db.session.add_all(menu_items)

    db.session.commit()
    click.echo(f"Created {len(restaurants_data)} restaurants with menu items.")


@click.command("seed-db")
def seed_db_command():
    seed_db()
    click.echo("Database seeded successfully.")


def init_seed_db_command(app):
    """Register the seed command with the Flask app."""

    app.cli.add_command(seed_db_command)
