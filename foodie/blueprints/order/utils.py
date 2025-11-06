from typing import Any

from foodie.models import Order, User, Restaurant, PaymentMethod, OrderItem, MenuItem


def prepare_order_for_list_template(
    order: Order,
    user: User,
    restaurant: Restaurant,
    payment_method: PaymentMethod | None,
) -> dict[str, Any]:
    """
    Prepare order data for list template rendering.

    Args:
        order: Order instance
        user: User instance
        restaurant: Restaurant instance
        payment_method: PaymentMethod instance or None

    Returns:
        Dictionary with order data formatted for template
    """
    return {
        "id": order.id,
        "user_id": order.user_id,
        "username": user.username,
        "full_name": user.full_name,
        "restaurant_name": restaurant.name,
        "country": restaurant.country,
        "total_amount": order.total_amount,
        "status": order.status,
        "payment_method_name": payment_method.name if payment_method else None,
        "created_at": order.created_at,
    }


def prepare_orders_for_list_template(
    orders: list[tuple[Order, User, Restaurant, PaymentMethod]],
) -> list[dict[str, Any]]:
    """
    Prepare a list of orders for list template rendering.

    Args:
        orders: List of tuples (order, user, restaurant, payment_method)

    Returns:
        List of dictionaries with order data formatted for template
    """
    order_list = []
    for order, user, restaurant, payment_method in orders:
        order_list.append(
            prepare_order_for_list_template(order, user, restaurant, payment_method)
        )
    return order_list


def prepare_order_for_view_template(
    order: Order,
    user: User,
    restaurant: Restaurant,
    payment_method: PaymentMethod | None,
) -> dict[str, Any]:
    """
    Prepare order data for view template rendering.

    Args:
        order: Order instance
        user: User instance
        restaurant: Restaurant instance
        payment_method: PaymentMethod instance or None

    Returns:
        Dictionary with order data formatted for template
    """
    return {
        "id": order.id,
        "user_id": order.user_id,
        "full_name": user.full_name,
        "restaurant_name": restaurant.name,
        "restaurant_country": restaurant.country,
        "status": order.status,
        "total_amount": order.total_amount,
        "payment_method_name": payment_method.name if payment_method else None,
        "created_at": order.created_at,
        "placed_at": order.placed_at,
        "cancelled_at": order.cancelled_at,
    }


def prepare_order_for_edit_template(
    order: Order, restaurant: Restaurant
) -> dict[str, Any]:
    """
    Prepare order data for edit template rendering.

    Args:
        order: Order instance
        restaurant: Restaurant instance

    Returns:
        Dictionary with order data formatted for template
    """
    return {
        "id": order.id,
        "user_id": order.user_id,
        "restaurant_id": restaurant.id,
        "restaurant_name": restaurant.name,
        "country": restaurant.country,
        "status": order.status,
        "total_amount": order.total_amount,
    }


def prepare_order_for_checkout_template(
    order: Order, restaurant: Restaurant
) -> dict[str, Any]:
    """
    Prepare order data for checkout template rendering.

    Args:
        order: Order instance
        restaurant: Restaurant instance

    Returns:
        Dictionary with order data formatted for template
    """
    return {
        "id": order.id,
        "restaurant_name": restaurant.name,
        "country": restaurant.country,
        "total_amount": order.total_amount,
    }


def prepare_order_item_for_template(
    order_item: OrderItem, menu_item: MenuItem, include_current_price: bool = False
) -> dict[str, Any]:
    """
    Prepare order item data for template rendering.

    Args:
        order_item: OrderItem instance
        menu_item: MenuItem instance
        include_current_price: Whether to include current menu item price

    Returns:
        Dictionary with order item data formatted for template
    """
    item_dict = {
        "id": order_item.id,
        "item_name": menu_item.name,
        "quantity": order_item.quantity,
        "unit_price": order_item.unit_price,
        "subtotal": order_item.subtotal,
    }
    if include_current_price:
        item_dict["current_price"] = menu_item.price
    return item_dict


def prepare_order_items_for_template(
    items: list[tuple[OrderItem, MenuItem]], include_current_price: bool = False
) -> list[dict[str, Any]]:
    """
    Prepare a list of order items for template rendering.

    Args:
        items: List of tuples (order_item, menu_item)
        include_current_price: Whether to include current menu item price

    Returns:
        List of dictionaries with order item data formatted for template
    """
    items_list = []
    for order_item, menu_item in items:
        items_list.append(
            prepare_order_item_for_template(
                order_item, menu_item, include_current_price
            )
        )
    return items_list
