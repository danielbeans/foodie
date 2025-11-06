import flask

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from foodie.db import db
from foodie.models import PaymentMethod, User, Restaurant, Order
from foodie.blueprints.auth import login_required, role_required

blueprint = flask.Blueprint("admin", __name__, url_prefix="/admin")


@blueprint.route("/")
@login_required
@role_required("ADMIN")
def dashboard() -> flask.Response:
    stats = {
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

    recent_orders = (
        db.session.query(Order, User, Restaurant)
        .join(User, Order.user_id == User.id)
        .join(Restaurant, Order.restaurant_id == Restaurant.id)
        .order_by(Order.created_at.desc())
        .limit(10)
        .all()
    )

    order_list = []
    for order, user, restaurant in recent_orders:
        order_dict = {
            "id": order.id,
            "full_name": user.full_name,
            "restaurant_name": restaurant.name,
            "total_amount": order.total_amount,
            "status": order.status,
            "created_at": order.created_at,
        }
        order_list.append(order_dict)

    return flask.render_template(
        "admin/dashboard.html", stats=stats, recent_orders=order_list
    )


@blueprint.route("/payment-methods")
@login_required
@role_required("ADMIN")
def list_payment_methods() -> flask.Response:
    payment_methods = db.session.query(PaymentMethod).order_by(PaymentMethod.name).all()
    return flask.render_template(
        "admin/payment_methods.html", payment_methods=payment_methods
    )


@blueprint.route("/payment-methods/add", methods=("GET", "POST"))
@login_required
@role_required("ADMIN")
def add_payment_method() -> flask.Response:
    if flask.request.method == "POST":
        name = flask.request.form["name"]
        description = flask.request.form.get("description", "")
        is_active = 1 if flask.request.form.get("is_active") else 0

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
                flask.flash(f'Payment method "{name}" added successfully.', "success")
                return flask.redirect(flask.url_for("admin.list_payment_methods"))
            except IntegrityError:
                db.session.rollback()
                error = f'Payment method "{name}" already exists.'

        if error:
            flask.flash(error, "danger")

    return flask.render_template("admin/add_payment_method.html")


@blueprint.route("/payment-methods/<int:method_id>/edit", methods=("GET", "POST"))
@login_required
@role_required("ADMIN")
def edit_payment_method(method_id: int) -> flask.Response:
    method = db.session.query(PaymentMethod).filter_by(id=method_id).first()

    if method is None:
        flask.flash("Payment method not found.", "danger")
        return flask.redirect(flask.url_for("admin.list_payment_methods"))

    if flask.request.method == "POST":
        name = flask.request.form["name"]
        description = flask.request.form.get("description", "")
        is_active = 1 if flask.request.form.get("is_active") else 0

        error = None

        if not name:
            error = "Payment method name is required."

        if error is None:
            method.name = name
            method.description = description
            method.is_active = is_active
            db.session.commit()
            flask.flash(f'Payment method "{name}" updated successfully.', "success")
            return flask.redirect(flask.url_for("admin.list_payment_methods"))

        flask.flash(error, "error")

    return flask.render_template("admin/edit_payment_method.html", method=method)


@blueprint.route("/payment-methods/<int:method_id>/toggle", methods=("POST",))
@login_required
@role_required("ADMIN")
def toggle_payment_method(method_id: int) -> flask.Response:
    method = db.session.query(PaymentMethod).filter_by(id=method_id).first()

    if method is None:
        flask.flash("Payment method not found.", "danger")
        return flask.redirect(flask.url_for("admin.list_payment_methods"))

    method.is_active = 0 if method.is_active else 1
    db.session.commit()

    status_text = "activated" if method.is_active else "deactivated"
    flask.flash(f'Payment method "{method.name}" {status_text}.', "success")
    return flask.redirect(flask.url_for("admin.list_payment_methods"))
