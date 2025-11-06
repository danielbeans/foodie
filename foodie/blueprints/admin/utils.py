from typing import Any

from foodie.models import Order, User, Restaurant


def prepare_order_for_template(
    order: Order, user: User, restaurant: Restaurant
) -> dict[str, Any]:
    """
    Prepare order data for template rendering.

    Args:
        order: Order instance
        user: User instance
        restaurant: Restaurant instance

    Returns:
        Dictionary with order data formatted for template
    """
    return {
        "id": order.id,
        "full_name": user.full_name,
        "restaurant_name": restaurant.name,
        "total_amount": order.total_amount,
        "status": order.status,
        "created_at": order.created_at,
    }


def prepare_orders_for_template(
    orders: list[tuple[Order, User, Restaurant]],
) -> list[dict[str, Any]]:
    """
    Prepare a list of orders for template rendering.

    Args:
        orders: List of tuples (order, user, restaurant)

    Returns:
        List of dictionaries with order data formatted for template
    """
    return [
        prepare_order_for_template(order, user, restaurant)
        for order, user, restaurant in orders
    ]
