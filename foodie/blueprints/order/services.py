import datetime

import flask_sqlalchemy
from sqlalchemy import func

from foodie.db import db
from foodie.models import (
    Order,
    Restaurant,
    User,
    OrderItem,
    MenuItem,
    PaymentMethod,
)


def get_orders_for_user(
    user_role: str, user_country: str | None = None
) -> list[tuple[Order, User, Restaurant, PaymentMethod]]:
    """
    Get orders accessible to the user based on their role and country.

    Args:
        user_role: User's role (ADMIN, MANAGER, MEMBER)
        user_country: User's country (required for non-admin users)

    Returns:
        List of tuples (order, user, restaurant, payment_method)
    """
    base_query = (
        db.session.query(Order, User, Restaurant, PaymentMethod)
        .join(User, Order.user_id == User.id)
        .join(Restaurant, Order.restaurant_id == Restaurant.id)
        .outerjoin(PaymentMethod, Order.payment_method_id == PaymentMethod.id)
    )

    if user_role == "ADMIN":
        # Admin can see all orders
        return base_query.order_by(Order.created_at.desc()).all()
    else:
        # Managers and Members can only see orders from their country
        return (
            base_query.filter(Restaurant.country == user_country)
            .order_by(Order.created_at.desc())
            .all()
        )


def get_order_by_id_with_relations(
    order_id: int,
) -> tuple[Order, User, Restaurant, PaymentMethod] | None:
    """
    Get an order by ID with related user, restaurant, and payment method.

    Args:
        order_id: Order ID

    Returns:
        Tuple (order, user, restaurant, payment_method) or None
    """
    return (
        db.session.query(Order, User, Restaurant, PaymentMethod)
        .join(User, Order.user_id == User.id)
        .join(Restaurant, Order.restaurant_id == Restaurant.id)
        .outerjoin(PaymentMethod, Order.payment_method_id == PaymentMethod.id)
        .filter(Order.id == order_id)
        .first()
    )


def get_order_by_id(order_id: int) -> Order | None:
    """
    Get an order by ID.

    Args:
        order_id: Order ID

    Returns:
        Order instance or None
    """
    return db.session.query(Order).filter_by(id=order_id).first()


def get_order_with_restaurant(order_id: int) -> tuple[Order, Restaurant] | None:
    """
    Get an order with its restaurant.

    Args:
        order_id: Order ID

    Returns:
        Tuple (order, restaurant) or None
    """
    return (
        db.session.query(Order, Restaurant)
        .join(Restaurant, Order.restaurant_id == Restaurant.id)
        .filter(Order.id == order_id)
        .first()
    )


def get_existing_draft_order(user_id: int, restaurant_id: int) -> Order | None:
    """
    Get an existing draft order for a user and restaurant.

    Args:
        user_id: User ID
        restaurant_id: Restaurant ID

    Returns:
        Order instance or None
    """
    return (
        db.session.query(Order)
        .filter_by(user_id=user_id, restaurant_id=restaurant_id, status="DRAFT")
        .first()
    )


def create_draft_order(user_id: int, restaurant_id: int) -> Order:
    """
    Create a new draft order.

    Args:
        user_id: User ID
        restaurant_id: Restaurant ID

    Returns:
        Created Order instance
    """
    new_order = Order(
        user_id=user_id,
        restaurant_id=restaurant_id,
        status="DRAFT",
        total_amount=0.0,
    )
    db.session.add(new_order)
    db.session.commit()
    return new_order


def get_order_items_with_menu_items(order_id: int) -> list[tuple[OrderItem, MenuItem]]:
    """
    Get order items with their menu items.

    Args:
        order_id: Order ID

    Returns:
        List of tuples (order_item, menu_item)
    """
    return (
        db.session.query(OrderItem, MenuItem)
        .join(MenuItem, OrderItem.menu_item_id == MenuItem.id)
        .filter(OrderItem.order_id == order_id)
        .all()
    )


def get_menu_item_with_restaurant(
    menu_item_id: int, restaurant_id: int
) -> tuple[MenuItem, Restaurant] | None:
    """
    Get a menu item with its restaurant, verifying it belongs to the restaurant.

    Args:
        menu_item_id: Menu item ID
        restaurant_id: Restaurant ID

    Returns:
        Tuple (menu_item, restaurant) or None
    """
    return (
        db.session.query(MenuItem, Restaurant)
        .join(Restaurant, MenuItem.restaurant_id == Restaurant.id)
        .filter(MenuItem.id == menu_item_id, MenuItem.restaurant_id == restaurant_id)
        .first()
    )


def get_existing_order_item(order_id: int, menu_item_id: int) -> OrderItem | None:
    """
    Get an existing order item if it exists.

    Args:
        order_id: Order ID
        menu_item_id: Menu item ID

    Returns:
        OrderItem instance or None
    """
    return (
        db.session.query(OrderItem)
        .filter_by(order_id=order_id, menu_item_id=menu_item_id)
        .first()
    )


def add_item_to_order(
    order_id: int, menu_item_id: int, quantity: int, unit_price: float
) -> None:
    """
    Add an item to an order or update quantity if it already exists.

    Args:
        order_id: Order ID
        menu_item_id: Menu item ID
        quantity: Quantity to add
        unit_price: Unit price
    """
    existing_item = get_existing_order_item(order_id, menu_item_id)

    if existing_item:
        existing_item.quantity += quantity
        existing_item.subtotal = existing_item.quantity * unit_price
    else:
        new_item = OrderItem(
            order_id=order_id,
            menu_item_id=menu_item_id,
            quantity=quantity,
            unit_price=unit_price,
            subtotal=quantity * unit_price,
        )
        db.session.add(new_item)


def remove_order_item(item_id: int, order_id: int) -> bool:
    """
    Remove an order item.

    Args:
        item_id: Order item ID
        order_id: Order ID

    Returns:
        True if item was found and removed, False otherwise
    """
    item = db.session.query(OrderItem).filter_by(id=item_id, order_id=order_id).first()
    if item:
        db.session.delete(item)
        return True
    return False


def update_order_total(db: flask_sqlalchemy.SQLAlchemy, order: Order) -> None:
    """
    Update the total amount of an order based on its items.

    Args:
        db: SQLAlchemy database instance
        order: Order instance
    """
    total = (
        db.session.query(func.coalesce(func.sum(OrderItem.subtotal), 0))
        .filter_by(order_id=order.id)
        .scalar()
    )
    order.total_amount = total


def get_order_item_count(order_id: int) -> int:
    """
    Get the count of items in an order.

    Args:
        order_id: Order ID

    Returns:
        Number of items in the order
    """
    return (
        db.session.query(func.count(OrderItem.id)).filter_by(order_id=order_id).scalar()
    )


def get_active_payment_methods() -> list[PaymentMethod]:
    """
    Get all active payment methods ordered by name.

    Returns:
        List of PaymentMethod instances
    """
    return (
        db.session.query(PaymentMethod)
        .filter_by(is_active=1)
        .order_by(PaymentMethod.name)
        .all()
    )


def get_payment_method_by_id(payment_method_id: int) -> PaymentMethod | None:
    """
    Get an active payment method by ID.

    Args:
        payment_method_id: Payment method ID

    Returns:
        PaymentMethod instance or None
    """
    return (
        db.session.query(PaymentMethod)
        .filter_by(id=payment_method_id, is_active=1)
        .first()
    )


def place_order_in_db(order_id: int, payment_method_id: int) -> None:
    """
    Place an order (change status from DRAFT to PLACED).

    Args:
        order_id: Order ID
        payment_method_id: Payment method ID
    """
    order = get_order_by_id(order_id)
    order.status = "PLACED"
    order.payment_method_id = payment_method_id
    order.placed_at = datetime.datetime.now(datetime.timezone.utc)
    db.session.commit()


def cancel_order_in_db(order_id: int) -> None:
    """
    Cancel an order.

    Args:
        order_id: Order ID
    """
    order = get_order_by_id(order_id)
    order.status = "CANCELLED"
    order.cancelled_at = datetime.datetime.now(datetime.timezone.utc)
    db.session.commit()


def update_order_payment_method(order_id: int, payment_method_id: int) -> None:
    """
    Update the payment method for a placed order.

    Args:
        order_id: Order ID
        payment_method_id: Payment method ID
    """
    order = get_order_by_id(order_id)
    order.payment_method_id = payment_method_id
    db.session.commit()


def can_user_edit_order(order: Order, user_id: int, user_role: str) -> bool:
    """
    Check if a user can edit an order.

    Args:
        order: Order instance
        user_id: User ID
        user_role: User role

    Returns:
        True if user can edit, False otherwise
    """
    if order.status != "DRAFT":
        return False
    if order.user_id == user_id:
        return True
    if user_role in ("ADMIN", "MANAGER"):
        return True
    return False


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
