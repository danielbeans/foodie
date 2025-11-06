"""
Order blueprint for managing orders (create, view, place, cancel).

Implements RBAC with the following permissions:
- ADMIN, MANAGER, MEMBER: Can create orders and add food items
- ADMIN, MANAGER: Can place orders (checkout & pay)
- ADMIN, MANAGER: Can cancel orders
- ADMIN only: Can update payment methods
"""

import datetime

import flask
import flask_sqlalchemy
from sqlalchemy import func

from foodie.db import db
from foodie.models import Order, Restaurant, User, OrderItem, MenuItem, PaymentMethod
from foodie.blueprints.auth import login_required, check_country_access, role_required

blueprint = flask.Blueprint("order", __name__, url_prefix="/orders")


@blueprint.route("/")
@login_required
def list_orders() -> flask.Response:
    if flask.g.user.role == "ADMIN":
        # Admin can see all orders
        orders = (
            db.session.query(Order, User, Restaurant, PaymentMethod)
            .join(User, Order.user_id == User.id)
            .join(Restaurant, Order.restaurant_id == Restaurant.id)
            .outerjoin(PaymentMethod, Order.payment_method_id == PaymentMethod.id)
            .order_by(Order.created_at.desc())
            .all()
        )
    else:
        # Managers and Members can only see orders from their country
        orders = (
            db.session.query(Order, User, Restaurant, PaymentMethod)
            .join(User, Order.user_id == User.id)
            .join(Restaurant, Order.restaurant_id == Restaurant.id)
            .outerjoin(PaymentMethod, Order.payment_method_id == PaymentMethod.id)
            .filter(Restaurant.country == flask.g.user.country)
            .order_by(Order.created_at.desc())
            .all()
        )

    # Convert to list of objects for template compatibility
    order_list = []
    for order, user, restaurant, payment_method in orders:
        order_dict = {
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
        order_list.append(order_dict)

    return flask.render_template("order/list.html", orders=order_list)


@blueprint.route("/<int:order_id>")
@login_required
def view_order(order_id: int) -> flask.Response:
    result = (
        db.session.query(Order, User, Restaurant, PaymentMethod)
        .join(User, Order.user_id == User.id)
        .join(Restaurant, Order.restaurant_id == Restaurant.id)
        .outerjoin(PaymentMethod, Order.payment_method_id == PaymentMethod.id)
        .filter(Order.id == order_id)
        .first()
    )

    if result is None:
        flask.flash("Order not found.", "warning")
        return flask.redirect(flask.url_for("order.list_orders"))

    order, user, restaurant, payment_method = result

    if not check_country_access(restaurant.country):
        flask.flash("You do not have permission to view this order.", "danger")
        return flask.redirect(flask.url_for("order.list_orders"))

    # Get order items
    items = (
        db.session.query(OrderItem, MenuItem)
        .join(MenuItem, OrderItem.menu_item_id == MenuItem.id)
        .filter(OrderItem.order_id == order_id)
        .all()
    )

    # Convert to objects for template
    order_dict = {
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

    items_list = []
    for order_item, menu_item in items:
        item_dict = {
            "id": order_item.id,
            "item_name": menu_item.name,
            "quantity": order_item.quantity,
            "unit_price": order_item.unit_price,
            "subtotal": order_item.subtotal,
        }
        items_list.append(item_dict)

    # Get payment methods for admin update feature
    payment_methods = None
    if flask.g.user and flask.g.user.role == "ADMIN" and order.status == "PLACED":
        payment_methods = (
            db.session.query(PaymentMethod)
            .filter_by(is_active=1)
            .order_by(PaymentMethod.name)
            .all()
        )

    return flask.render_template(
        "order/view.html",
        order=order_dict,
        items=items_list,
        payment_methods=payment_methods,
    )


@blueprint.route("/create/<int:restaurant_id>", methods=("GET", "POST"))
@login_required
def create_order(restaurant_id: int) -> flask.Response:
    restaurant = db.session.query(Restaurant).filter_by(id=restaurant_id).first()

    if restaurant is None:
        flask.flash("Restaurant not found.", "danger")
        return flask.redirect(flask.url_for("restaurant.list_restaurants"))

    if not check_country_access(restaurant.country):
        flask.flash(
            "You do not have permission to order from this restaurant.", "danger"
        )
        return flask.redirect(flask.url_for("restaurant.list_restaurants"))

    existing_draft = (
        db.session.query(Order)
        .filter_by(user_id=flask.g.user.id, restaurant_id=restaurant_id, status="DRAFT")
        .first()
    )

    if existing_draft:
        return flask.redirect(
            flask.url_for("order.edit_order", order_id=existing_draft.id)
        )

    new_order = Order(
        user_id=flask.g.user.id,
        restaurant_id=restaurant_id,
        status="DRAFT",
        total_amount=0.0,
    )
    db.session.add(new_order)
    db.session.commit()

    flask.flash("Order created! Add items to your cart.", "success")
    return flask.redirect(flask.url_for("order.edit_order", order_id=new_order.id))


@blueprint.route("/<int:order_id>/edit")
@login_required
def edit_order(order_id: int) -> flask.Response:
    result = (
        db.session.query(Order, Restaurant)
        .join(Restaurant, Order.restaurant_id == Restaurant.id)
        .filter(Order.id == order_id)
        .first()
    )
    if result is None:
        flask.flash("Order not found.", "danger")
        return flask.redirect(flask.url_for("order.list_orders"))

    order, restaurant = result

    # Check if order belongs to user and is still a draft
    if (
        order.user_id != flask.g.user.id
        and flask.g.user.role != "ADMIN"
        and flask.g.user.role != "MANAGER"
    ):
        flask.flash("You do not have permission to edit this order.", "danger")
        return flask.redirect(flask.url_for("order.list_orders"))

    if order.status != "DRAFT":
        flask.flash("This order has already been placed and cannot be edited.", "info")
        return flask.redirect(flask.url_for("order.view_order", order_id=order_id))

    items = (
        db.session.query(OrderItem, MenuItem)
        .join(MenuItem, OrderItem.menu_item_id == MenuItem.id)
        .filter(OrderItem.order_id == order_id)
        .all()
    )
    menu_items = (
        db.session.query(MenuItem)
        .filter_by(restaurant_id=restaurant.id)
        .order_by(MenuItem.name)
        .all()
    )

    # Convert to format for template
    order_dict = {
        "id": order.id,
        "user_id": order.user_id,
        "restaurant_id": restaurant.id,
        "restaurant_name": restaurant.name,
        "country": restaurant.country,
        "status": order.status,
        "total_amount": order.total_amount,
    }

    items_list = []
    for order_item, menu_item in items:
        item_dict = {
            "id": order_item.id,
            "item_name": menu_item.name,
            "quantity": order_item.quantity,
            "unit_price": order_item.unit_price,
            "subtotal": order_item.subtotal,
            "current_price": menu_item.price,
        }
        items_list.append(item_dict)

    return flask.render_template(
        "order/edit.html", order=order_dict, items=items_list, menu_items=menu_items
    )


@blueprint.route("/<int:order_id>/add-item", methods=("POST",))
@login_required
def add_item(order_id: int) -> flask.Response:
    menu_item_id = flask.request.form.get("menu_item_id", type=int)
    quantity = flask.request.form.get("quantity", 1, type=int)

    order = (
        db.session.query(Order)
        .filter_by(id=order_id, user_id=flask.g.user.id, status="DRAFT")
        .first()
    )

    if order is None:
        flask.flash("Order not found or cannot be modified.", "danger")
        return flask.redirect(flask.url_for("order.list_orders"))

    menu_item = (
        db.session.query(MenuItem, Restaurant)
        .join(Restaurant, MenuItem.restaurant_id == Restaurant.id)
        .filter(
            MenuItem.id == menu_item_id,
            MenuItem.restaurant_id == order.restaurant_id,
        )
        .first()
    )

    if menu_item is None:
        flask.flash("Menu item not found.", "danger")
        return flask.redirect(flask.url_for("order.edit_order", order_id=order_id))

    menu_item, restaurant = menu_item

    existing_item = (
        db.session.query(OrderItem)
        .filter_by(order_id=order_id, menu_item_id=menu_item_id)
        .first()
    )

    if existing_item:
        existing_item.quantity += quantity
        existing_item.subtotal = existing_item.quantity * menu_item.price
    else:
        new_item = OrderItem(
            order_id=order_id,
            menu_item_id=menu_item_id,
            quantity=quantity,
            unit_price=menu_item.price,
            subtotal=quantity * menu_item.price,
        )
        db.session.add(new_item)

    update_order_total(db, order)
    db.session.commit()

    flask.flash(f"Added {menu_item.name} to cart.", "success")
    return flask.redirect(flask.url_for("order.edit_order", order_id=order_id))


@blueprint.route("/<int:order_id>/remove-item/<int:item_id>", methods=("POST",))
@login_required
def remove_item(order_id: int, item_id: int) -> flask.Response:
    order = (
        db.session.query(Order)
        .filter_by(id=order_id, user_id=flask.g.user.id, status="DRAFT")
        .first()
    )

    if order is None:
        flask.flash("Order not found or cannot be modified.", "error")
        return flask.redirect(flask.url_for("order.list_orders"))

    item = db.session.query(OrderItem).filter_by(id=item_id, order_id=order_id).first()
    if item:
        db.session.delete(item)

    update_order_total(db, order)
    db.session.commit()

    flask.flash("Item removed from cart.", "success")
    return flask.redirect(flask.url_for("order.edit_order", order_id=order_id))


@blueprint.route("/<int:order_id>/place", methods=("GET", "POST"))
@login_required
@role_required("ADMIN", "MANAGER")
def place_order(order_id: int) -> flask.Response:
    result = (
        db.session.query(Order, Restaurant)
        .join(Restaurant, Order.restaurant_id == Restaurant.id)
        .filter(Order.id == order_id)
        .first()
    )

    if result is None:
        flask.flash("Order not found.", "danger")
        return flask.redirect(flask.url_for("order.list_orders"))

    order, restaurant = result

    if order.status != "DRAFT":
        flask.flash("This order has already been placed.", "info")
        return flask.redirect(flask.url_for("order.view_order", order_id=order_id))

    item_count = (
        db.session.query(func.count(OrderItem.id)).filter_by(order_id=order_id).scalar()
    )

    if item_count == 0:
        flask.flash("Cannot place an empty order. Please add items first.", "error")
        return flask.redirect(flask.url_for("order.edit_order", order_id=order_id))

    if flask.request.method == "POST":
        payment_method_id = flask.request.form.get("payment_method_id", type=int)

        if not payment_method_id:
            flask.flash("Please select a payment method.", "error")
            return flask.redirect(flask.url_for("order.place_order", order_id=order_id))

        # Verify payment method exists and is active
        payment_method = (
            db.session.query(PaymentMethod)
            .filter_by(id=payment_method_id, is_active=1)
            .first()
        )

        if payment_method is None:
            flask.flash("Invalid payment method.", "danger")
            return flask.redirect(flask.url_for("order.place_order", order_id=order_id))

        order.status = "PLACED"
        order.payment_method_id = payment_method_id
        order.placed_at = datetime.datetime.now(datetime.timezone.utc)
        db.session.commit()

        flask.flash("Order placed successfully!", "success")
        return flask.redirect(flask.url_for("order.view_order", order_id=order_id))

    # GET request - show checkout page
    payment_methods = (
        db.session.query(PaymentMethod)
        .filter_by(is_active=1)
        .order_by(PaymentMethod.name)
        .all()
    )

    items = (
        db.session.query(OrderItem, MenuItem)
        .join(MenuItem, OrderItem.menu_item_id == MenuItem.id)
        .filter(OrderItem.order_id == order_id)
        .all()
    )

    # Format for template
    order_dict = {
        "id": order.id,
        "restaurant_name": restaurant.name,
        "country": restaurant.country,
        "total_amount": order.total_amount,
    }

    items_list = []
    for order_item, menu_item in items:
        item_dict = {
            "item_name": menu_item.name,
            "quantity": order_item.quantity,
            "unit_price": order_item.unit_price,
            "subtotal": order_item.subtotal,
        }
        items_list.append(item_dict)

    return flask.render_template(
        "order/checkout.html",
        order=order_dict,
        items=items_list,
        payment_methods=payment_methods,
    )


@blueprint.route("/<int:order_id>/cancel", methods=("POST",))
@login_required
@role_required("ADMIN", "MANAGER")
def cancel_order(order_id: int) -> flask.Response:
    result = (
        db.session.query(Order, User)
        .join(User, Order.user_id == User.id)
        .filter(Order.id == order_id)
        .first()
    )

    if result is None:
        flask.flash("Order not found.", "danger")
        return flask.redirect(flask.url_for("order.list_orders"))

    order, user = result

    if not check_country_access(user.country):
        flask.flash("You do not have permission to cancel this order.", "danger")
        return flask.redirect(flask.url_for("order.list_orders"))

    if order.status == "CANCELLED":
        flask.flash("This order is already cancelled.", "info")
        return flask.redirect(flask.url_for("order.view_order", order_id=order_id))

    if order.status == "COMPLETED":
        flask.flash("Cannot cancel a completed order.", "danger")
        return flask.redirect(flask.url_for("order.view_order", order_id=order_id))

    order.status = "CANCELLED"
    order.cancelled_at = datetime.datetime.now(datetime.timezone.utc)
    db.session.commit()

    flask.flash("Order cancelled successfully.", "success")
    return flask.redirect(flask.url_for("order.view_order", order_id=order_id))


@blueprint.route("/<int:order_id>/update-payment", methods=("POST",))
@login_required
@role_required("ADMIN")
def update_payment_method(order_id: int) -> flask.Response:
    payment_method_id = flask.request.form.get("payment_method_id", type=int)

    order = db.session.query(Order).filter_by(id=order_id).first()

    if order is None:
        flask.flash("Order not found.", "danger")
        return flask.redirect(flask.url_for("order.list_orders"))

    # Verify payment method exists and is active
    payment_method = (
        db.session.query(PaymentMethod)
        .filter_by(id=payment_method_id, is_active=1)
        .first()
    )

    if payment_method is None:
        flask.flash("Invalid payment method.", "danger")
        return flask.redirect(flask.url_for("order.view_order", order_id=order_id))

    order.payment_method_id = payment_method_id
    db.session.commit()

    flask.flash("Payment method updated successfully.", "success")
    return flask.redirect(flask.url_for("order.view_order", order_id=order_id))


def update_order_total(db: flask_sqlalchemy.SQLAlchemy, order: Order) -> None:
    total = (
        db.session.query(func.coalesce(func.sum(OrderItem.subtotal), 0))
        .filter_by(order_id=order.id)
        .scalar()
    )
    order.total_amount = total
