from typing import Any

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from foodie.db import db
from foodie.models import PaymentMethod, User, Restaurant, Order


def get_dashboard_stats() -> dict[str, Any]:
    """
    Get statistics for the admin dashboard.

    Returns:
        Dictionary with dashboard statistics
    """
    return {
        "total_users": db.session.query(func.count(User.id)).scalar(),
        "total_restaurants": db.session.query(func.count(Restaurant.id)).scalar(),
        "total_orders": db.session.query(func.count(Order.id)).scalar(),
        "placed_orders": db.session.query(func.count(Order.id))
        .filter(Order.status == "PLACED")
        .scalar(),
        "total_revenue": db.session.query(
            func.coalesce(func.sum(Order.total_amount), 0)
        )
        .filter(Order.status.in_(["PLACED", "COMPLETED"]))
        .scalar(),
    }


def get_recent_orders(limit: int = 10) -> list[tuple[Order, User, Restaurant]]:
    """
    Get recent orders for the admin dashboard.

    Args:
        limit: Maximum number of orders to return

    Returns:
        List of tuples (order, user, restaurant)
    """
    return (
        db.session.query(Order, User, Restaurant)
        .join(User, Order.user_id == User.id)
        .join(Restaurant, Order.restaurant_id == Restaurant.id)
        .order_by(Order.created_at.desc())
        .limit(limit)
        .all()
    )


def get_all_payment_methods() -> list[PaymentMethod]:
    """
    Get all payment methods ordered by name.

    Returns:
        List of PaymentMethod instances
    """
    return db.session.query(PaymentMethod).order_by(PaymentMethod.name).all()


def get_payment_method_by_id(method_id: int) -> PaymentMethod | None:
    """
    Get a payment method by ID.

    Args:
        method_id: Payment method ID

    Returns:
        PaymentMethod instance or None
    """
    return db.session.query(PaymentMethod).filter_by(id=method_id).first()


def create_payment_method(
    name: str, description: str = "", is_active: int = 1
) -> tuple[PaymentMethod, str | None]:
    """
    Create a new payment method.

    Args:
        name: Payment method name
        description: Payment method description
        is_active: Whether the payment method is active (1 or 0)

    Returns:
        Tuple of (PaymentMethod instance, error message if any)
    """
    error = None

    if not name:
        error = "Payment method name is required."

    if error is None:
        try:
            method = PaymentMethod(
                name=name, description=description, is_active=is_active
            )
            db.session.add(method)
            db.session.commit()
            return method, None
        except IntegrityError:
            db.session.rollback()
            error = f'Payment method "{name}" already exists.'

    return None, error


def update_payment_method(
    method_id: int, name: str, description: str = "", is_active: int = 1
) -> str | None:
    """
    Update an existing payment method.

    Args:
        method_id: Payment method ID
        name: Payment method name
        description: Payment method description
        is_active: Whether the payment method is active (1 or 0)

    Returns:
        Error message if any, None otherwise
    """
    method = get_payment_method_by_id(method_id)
    if method is None:
        return "Payment method not found."

    error = None

    if not name:
        error = "Payment method name is required."

    if error is None:
        method.name = name
        method.description = description
        method.is_active = is_active
        db.session.commit()

    return error


def toggle_payment_method_status(
    method_id: int,
) -> tuple[PaymentMethod | None, str | None]:
    """
    Toggle the active status of a payment method.

    Args:
        method_id: Payment method ID

    Returns:
        Tuple of (PaymentMethod instance or None, error message if any)
    """
    method = get_payment_method_by_id(method_id)

    if method is None:
        return None, "Payment method not found."

    method.is_active = 0 if method.is_active else 1
    db.session.commit()

    return method, None
