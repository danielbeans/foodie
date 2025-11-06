"""
Order routes for managing orders (create, view, place, cancel).

Implements RBAC with the following permissions:
- ADMIN, MANAGER, MEMBER: Can create orders and add food items
- ADMIN, MANAGER: Can place orders (checkout & pay)
- ADMIN, MANAGER: Can cancel orders
- ADMIN only: Can update payment methods
"""

import flask

from foodie.db import db
from foodie.models import Order
from foodie.blueprints.auth.utils import (
    login_required,
    check_country_access,
    role_required,
)
from foodie.blueprints.order.services import (
    get_orders_for_user,
    get_order_by_id_with_relations,
    get_order_with_restaurant,
    get_existing_draft_order,
    create_draft_order,
    get_order_items_with_menu_items,
    get_menu_item_with_restaurant,
    add_item_to_order,
    remove_order_item,
    update_order_total,
    get_order_item_count,
    get_active_payment_methods,
    get_payment_method_by_id,
    place_order_in_db,
    cancel_order_in_db,
    update_order_payment_method,
    can_user_edit_order,
    get_menu_items_for_restaurant,
)
from foodie.blueprints.order.utils import (
    prepare_orders_for_list_template,
    prepare_order_for_view_template,
    prepare_order_for_edit_template,
    prepare_order_for_checkout_template,
    prepare_order_items_for_template,
)

blueprint = flask.Blueprint("order", __name__, url_prefix="/orders")


@blueprint.route("/")
@login_required
def list_orders() -> flask.Response:
    orders = get_orders_for_user(
        flask.g.user.role, flask.g.user.country if flask.g.user else None
    )
    order_list = prepare_orders_for_list_template(orders)

    return flask.render_template("order/list.html", orders=order_list)


@blueprint.route("/<int:order_id>")
@login_required
def view_order(order_id: int) -> flask.Response:
    result = get_order_by_id_with_relations(order_id)

    if result is None:
        flask.flash("Order not found.", "warning")
        return flask.redirect(flask.url_for("order.list_orders"))

    order, user, restaurant, payment_method = result

    if not check_country_access(restaurant.country):
        flask.flash("You do not have permission to view this order.", "danger")
        return flask.redirect(flask.url_for("order.list_orders"))

    items = get_order_items_with_menu_items(order_id)
    items_list = prepare_order_items_for_template(items)

    order_dict = prepare_order_for_view_template(
        order, user, restaurant, payment_method
    )

    # Get payment methods for admin update feature
    payment_methods = None
    if flask.g.user and flask.g.user.role == "ADMIN" and order.status == "PLACED":
        payment_methods = get_active_payment_methods()

    return flask.render_template(
        "order/view.html",
        order=order_dict,
        items=items_list,
        payment_methods=payment_methods,
    )


@blueprint.route("/create/<int:restaurant_id>", methods=("GET", "POST"))
@login_required
def create_order(restaurant_id: int) -> flask.Response:
    from foodie.blueprints.restaurant.services import get_restaurant_by_id

    restaurant = get_restaurant_by_id(restaurant_id)

    if restaurant is None:
        flask.flash("Restaurant not found.", "danger")
        return flask.redirect(flask.url_for("restaurant.list_restaurants"))

    if not check_country_access(restaurant.country):
        flask.flash(
            "You do not have permission to order from this restaurant.", "danger"
        )
        return flask.redirect(flask.url_for("restaurant.list_restaurants"))

    existing_draft = get_existing_draft_order(flask.g.user.id, restaurant_id)

    if existing_draft:
        return flask.redirect(
            flask.url_for("order.edit_order", order_id=existing_draft.id)
        )

    new_order = create_draft_order(flask.g.user.id, restaurant_id)

    flask.flash("Order created! Add items to your cart.", "success")
    return flask.redirect(flask.url_for("order.edit_order", order_id=new_order.id))


@blueprint.route("/<int:order_id>/edit")
@login_required
def edit_order(order_id: int) -> flask.Response:
    result = get_order_with_restaurant(order_id)
    if result is None:
        flask.flash("Order not found.", "danger")
        return flask.redirect(flask.url_for("order.list_orders"))

    order, restaurant = result

    # Check if order belongs to user and is still a draft
    if not can_user_edit_order(order, flask.g.user.id, flask.g.user.role):
        flask.flash("You do not have permission to edit this order.", "danger")
        return flask.redirect(flask.url_for("order.list_orders"))

    if order.status != "DRAFT":
        flask.flash("This order has already been placed and cannot be edited.", "info")
        return flask.redirect(flask.url_for("order.view_order", order_id=order_id))

    items = get_order_items_with_menu_items(order_id)
    menu_items = get_menu_items_for_restaurant(restaurant.id)

    order_dict = prepare_order_for_edit_template(order, restaurant)
    items_list = prepare_order_items_for_template(items, include_current_price=True)

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

    menu_item_result = get_menu_item_with_restaurant(menu_item_id, order.restaurant_id)

    if menu_item_result is None:
        flask.flash("Menu item not found.", "danger")
        return flask.redirect(flask.url_for("order.edit_order", order_id=order_id))

    menu_item, restaurant = menu_item_result

    add_item_to_order(order_id, menu_item_id, quantity, menu_item.price)

    update_order_total(db, order)
    db.session.commit()

    flask.flash(f"Added {menu_item.name} to cart.", "success")
    return flask.redirect(flask.url_for("order.edit_order", order_id=order_id))


@blueprint.route("/<int:order_id>/remove-item/<int:item_id>", methods=("POST",))
@login_required
def remove_item(order_id: int, item_id: int) -> flask.Response:
    from foodie.models import Order

    order = db.session.query(Order).filter_by(id=order_id, status="DRAFT").first()

    if order is None:
        flask.flash("Order not found or cannot be modified.", "danger")
        return flask.redirect(flask.url_for("order.list_orders"))

    remove_order_item(item_id, order_id)

    update_order_total(db, order)
    db.session.commit()

    flask.flash("Item removed from cart.", "success")
    return flask.redirect(flask.url_for("order.edit_order", order_id=order_id))


@blueprint.route("/<int:order_id>/place", methods=("GET", "POST"))
@login_required
@role_required("ADMIN", "MANAGER")
def place_order(order_id: int) -> flask.Response:
    result = get_order_with_restaurant(order_id)

    if result is None:
        flask.flash("Order not found.", "danger")
        return flask.redirect(flask.url_for("order.list_orders"))

    order, restaurant = result

    if order.status != "DRAFT":
        flask.flash("This order has already been placed.", "info")
        return flask.redirect(flask.url_for("order.view_order", order_id=order_id))

    item_count = get_order_item_count(order_id)

    if item_count == 0:
        flask.flash("Cannot place an empty order. Please add items first.", "danger")
        return flask.redirect(flask.url_for("order.edit_order", order_id=order_id))

    if flask.request.method == "POST":
        payment_method_id = flask.request.form.get("payment_method_id", type=int)

        if not payment_method_id:
            flask.flash("Please select a payment method.", "danger")
            return flask.redirect(flask.url_for("order.place_order", order_id=order_id))

        # Verify payment method exists and is active
        payment_method = get_payment_method_by_id(payment_method_id)

        if payment_method is None:
            flask.flash("Invalid payment method.", "danger")
            return flask.redirect(flask.url_for("order.place_order", order_id=order_id))

        place_order_in_db(order_id, payment_method_id)

        flask.flash("Order placed successfully!", "success")
        return flask.redirect(flask.url_for("order.view_order", order_id=order_id))

    # GET request - show checkout page
    payment_methods = get_active_payment_methods()
    items = get_order_items_with_menu_items(order_id)

    order_dict = prepare_order_for_checkout_template(order, restaurant)
    items_list = prepare_order_items_for_template(items)

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
    result = get_order_by_id_with_relations(order_id)

    if result is None:
        flask.flash("Order not found.", "danger")
        return flask.redirect(flask.url_for("order.list_orders"))

    order, user, restaurant, payment_method = result

    if not check_country_access(user.country):
        flask.flash("You do not have permission to cancel this order.", "danger")
        return flask.redirect(flask.url_for("order.list_orders"))

    if order.status == "CANCELLED":
        flask.flash("This order is already cancelled.", "info")
        return flask.redirect(flask.url_for("order.view_order", order_id=order_id))

    if order.status == "COMPLETED":
        flask.flash("Cannot cancel a completed order.", "danger")
        return flask.redirect(flask.url_for("order.view_order", order_id=order_id))

    cancel_order_in_db(order_id)

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
    payment_method = get_payment_method_by_id(payment_method_id)

    if payment_method is None:
        flask.flash("Invalid payment method.", "danger")
        return flask.redirect(flask.url_for("order.view_order", order_id=order_id))

    update_order_payment_method(order_id, payment_method_id)

    flask.flash("Payment method updated successfully.", "success")
    return flask.redirect(flask.url_for("order.view_order", order_id=order_id))
