import flask

from foodie.blueprints.auth.utils import login_required, check_country_access
from foodie.blueprints.restaurant.services import (
    get_restaurants_for_user,
    get_restaurant_by_id,
    get_menu_items_for_restaurant,
)
from foodie.blueprints.restaurant.utils import prepare_restaurants_for_template

blueprint = flask.Blueprint("restaurant", __name__, url_prefix="/restaurants")


@blueprint.route("/")
@login_required
def list_restaurants() -> flask.Response:
    restaurants = get_restaurants_for_user(
        flask.g.user.role, flask.g.user.country if flask.g.user else None
    )
    restaurant_list = prepare_restaurants_for_template(restaurants)

    return flask.render_template("restaurant/list.html", restaurants=restaurant_list)


@blueprint.route("/<int:restaurant_id>")
@login_required
def view_restaurant(restaurant_id: int) -> flask.Response:
    restaurant = get_restaurant_by_id(restaurant_id)

    if restaurant is None:
        flask.flash("Restaurant not found.", "danger")
        return flask.redirect(flask.url_for("restaurant.list_restaurants"))

    # Check if user has access to this restaurant's country
    if not check_country_access(restaurant.country):
        flask.flash("You do not have permission to view this restaurant.", "danger")
        return flask.redirect(flask.url_for("restaurant.list_restaurants"))

    menu_items = get_menu_items_for_restaurant(restaurant_id)

    return flask.render_template(
        "restaurant/view.html", restaurant=restaurant, items=menu_items
    )
