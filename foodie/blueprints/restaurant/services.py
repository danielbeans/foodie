from sqlalchemy import func

from foodie.db import db
from foodie.models import Restaurant, MenuItem


def get_restaurants_for_user(
    user_role: str,
    user_country: str | None = None,
) -> list[tuple[Restaurant, int]]:
    """
    Get restaurants accessible to the user based on their role and country.

    Args:
        user_role: User's role (ADMIN, MANAGER, MEMBER)
        user_country: User's country (required for non-admin users)

    Returns:
        List of tuples (restaurant, menu_count)
    """
    if user_role == "ADMIN":
        # Admin can see all restaurants
        return (
            db.session.query(
                Restaurant,
                func.count(MenuItem.id).label("menu_count"),
            )
            .outerjoin(MenuItem, (Restaurant.id == MenuItem.restaurant_id))
            .group_by(Restaurant.id)
            .order_by(Restaurant.country, Restaurant.name)
            .all()
        )
    else:
        # Managers and Members can only see restaurants in their country
        return (
            db.session.query(
                Restaurant,
                func.count(MenuItem.id).label("menu_count"),
            )
            .outerjoin(MenuItem, (Restaurant.id == MenuItem.restaurant_id))
            .filter(Restaurant.country == user_country)
            .group_by(Restaurant.id)
            .order_by(Restaurant.name)
            .all()
        )


def get_restaurant_by_id(restaurant_id: int) -> Restaurant | None:
    """
    Get a restaurant by ID.

    Args:
        restaurant_id: Restaurant ID

    Returns:
        Restaurant instance or None
    """
    return db.session.query(Restaurant).filter_by(id=restaurant_id).first()


def get_menu_items_for_restaurant(restaurant_id: int) -> list[MenuItem]:
    """
    Get menu items for a restaurant.

    Args:
        restaurant_id: Restaurant ID

    Returns:
        List of MenuItem instances
    """
    return (
        db.session.query(MenuItem)
        .filter_by(restaurant_id=restaurant_id)
        .order_by(MenuItem.name)
        .all()
    )
