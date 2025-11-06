from typing import Any

from foodie.models import Restaurant


def prepare_restaurant_for_template(
    restaurant: Restaurant, menu_count: int = 0
) -> dict[str, Any]:
    """
    Prepare restaurant data for template rendering.

    Args:
        restaurant: Restaurant instance
        menu_count: Number of menu items

    Returns:
        Dictionary with restaurant data formatted for template
    """
    return {
        "id": restaurant.id,
        "name": restaurant.name,
        "description": restaurant.description,
        "country": restaurant.country,
        "address": restaurant.address,
        "phone": restaurant.phone,
        "menu_count": menu_count,
    }


def prepare_restaurants_for_template(
    restaurants: list[tuple[Restaurant, int]],
) -> list[dict[str, Any]]:
    """
    Prepare a list of restaurants for template rendering.

    Args:
        restaurants: List of tuples (restaurant, menu_count)

    Returns:
        List of dictionaries with restaurant data formatted for template
    """
    restaurant_list = []
    for restaurant, menu_count in restaurants:
        restaurant_list.append(prepare_restaurant_for_template(restaurant, menu_count))
    return restaurant_list
