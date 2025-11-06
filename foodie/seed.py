"""
Seed the database with initial data using SQLAlchemy models.
Run with: uv run flask --app foodie seed-db
"""

import click
import json
import pathlib
from typing import Any
from werkzeug.security import generate_password_hash

import flask

from foodie.db import db
from foodie.models import User, Restaurant, MenuItem, PaymentMethod


def load_seed_data() -> dict[str, Any]:
    seed_file = pathlib.Path(__file__).parent.parent / "seed_data.json"
    with seed_file.open() as f:
        return json.load(f)


def seed_db() -> None:
    """Seed the database with initial data from JSON file."""

    app = flask.current_app

    with app.app_context():
        data = load_seed_data()
        create_payment_methods(data.get("payment_methods", []))
        create_users(data["users"])
        create_restaurants(data["restaurants"])


def create_payment_methods(payment_methods_data: list[dict[str, Any]]) -> None:
    """Create payment methods from JSON data."""

    payment_methods = []
    for method_data in payment_methods_data:
        payment_method = PaymentMethod(
            name=method_data["name"],
            description=method_data.get("description", ""),
            is_active=method_data.get("is_active", 1),
        )
        payment_methods.append(payment_method)

    db.session.add_all(payment_methods)
    db.session.commit()
    click.echo(f"Created {len(payment_methods)} payment methods.")


def create_users(users_data: list[dict[str, Any]]) -> None:
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


def create_restaurants(restaurants_data: list[dict[str, Any]]) -> None:
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
def seed_db_command() -> None:
    seed_db()
    click.echo("Database seeded successfully.")


def init_seed_db_command(app: flask.Flask) -> None:
    """Register the seed command with the Flask app."""

    app.cli.add_command(seed_db_command)
