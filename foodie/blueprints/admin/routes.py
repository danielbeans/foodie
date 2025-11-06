import flask

from foodie.blueprints.auth.utils import login_required, role_required
from foodie.blueprints.admin.services import (
    get_dashboard_stats,
    get_recent_orders,
    get_all_payment_methods,
    get_payment_method_by_id,
    create_payment_method,
    update_payment_method,
    toggle_payment_method_status,
)
from foodie.blueprints.admin.utils import prepare_orders_for_template

blueprint = flask.Blueprint("admin", __name__, url_prefix="/admin")


@blueprint.route("/")
@login_required
@role_required("ADMIN")
def dashboard() -> flask.Response:
    stats = get_dashboard_stats()
    recent_orders = get_recent_orders()
    order_list = prepare_orders_for_template(recent_orders)

    return flask.render_template(
        "admin/dashboard.html", stats=stats, recent_orders=order_list
    )


@blueprint.route("/payment-methods")
@login_required
@role_required("ADMIN")
def list_payment_methods() -> flask.Response:
    payment_methods = get_all_payment_methods()
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

        method, error = create_payment_method(name, description, is_active)

        if error:
            flask.flash(error, "danger")
        else:
            flask.flash(f'Payment method "{name}" added successfully.', "success")
            return flask.redirect(flask.url_for("admin.list_payment_methods"))

    return flask.render_template("admin/add_payment_method.html")


@blueprint.route("/payment-methods/<int:method_id>/edit", methods=("GET", "POST"))
@login_required
@role_required("ADMIN")
def edit_payment_method(method_id: int) -> flask.Response:
    method = get_payment_method_by_id(method_id)

    if method is None:
        flask.flash("Payment method not found.", "danger")
        return flask.redirect(flask.url_for("admin.list_payment_methods"))

    if flask.request.method == "POST":
        name = flask.request.form["name"]
        description = flask.request.form.get("description", "")
        is_active = 1 if flask.request.form.get("is_active") else 0

        error = update_payment_method(method_id, name, description, is_active)

        if error:
            flask.flash(error, "danger")
        else:
            flask.flash(f'Payment method "{name}" updated successfully.', "success")
            return flask.redirect(flask.url_for("admin.list_payment_methods"))

    return flask.render_template("admin/edit_payment_method.html", method=method)


@blueprint.route("/payment-methods/<int:method_id>/toggle", methods=("POST",))
@login_required
@role_required("ADMIN")
def toggle_payment_method(method_id: int) -> flask.Response:
    method, error = toggle_payment_method_status(method_id)

    if error:
        flask.flash(error, "danger")
        return flask.redirect(flask.url_for("admin.list_payment_methods"))

    status_text = "activated" if method.is_active else "deactivated"
    flask.flash(f'Payment method "{method.name}" {status_text}.', "success")
    return flask.redirect(flask.url_for("admin.list_payment_methods"))
