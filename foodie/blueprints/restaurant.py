import flask
from sqlalchemy import func
from foodie.db import db
from foodie.models import Restaurant, MenuItem
from foodie.blueprints.auth import login_required, check_country_access

blueprint = flask.Blueprint("restaurant", __name__, url_prefix="/restaurants")


@blueprint.route("/")
@login_required
def list_restaurants():
    if flask.g.user.role == "ADMIN":
        # Admin can see all restaurants
        restaurants = (
            db.session.query(
                Restaurant,
                func.count(MenuItem.id).label("menu_count"),
            )
            .outerjoin(MenuItem, (Restaurant.id == MenuItem.restaurant_id))
            .group_by(Restaurant.id)
            .order_by(Restaurant.country, Restaurant.name)
            .all()
        )
    else:
        # Managers and Members can only see restaurants in their country
        restaurants = (
            db.session.query(
                Restaurant,
                func.count(MenuItem.id).label("menu_count"),
            )
            .outerjoin(MenuItem, (Restaurant.id == MenuItem.restaurant_id))
            .filter(Restaurant.country == flask.g.user.country)
            .group_by(Restaurant.id)
            .order_by(Restaurant.name)
            .all()
        )

    # Convert to list of dicts for template compatibility
    restaurant_list = []
    for restaurant, menu_count in restaurants:
        restaurant_dict = {
            "id": restaurant.id,
            "name": restaurant.name,
            "description": restaurant.description,
            "country": restaurant.country,
            "address": restaurant.address,
            "phone": restaurant.phone,
            "menu_count": menu_count,
        }
        restaurant_list.append(restaurant_dict)

    return flask.render_template("restaurant/list.html", restaurants=restaurant_list)


@blueprint.route("/<int:restaurant_id>")
@login_required
def view_restaurant(restaurant_id):
    restaurant = db.session.query(Restaurant).filter_by(id=restaurant_id).first()

    if restaurant is None:
        flask.flash("Restaurant not found.", "error")
        return flask.redirect(flask.url_for("restaurant.list_restaurants"))

    # Check if user has access to this restaurant's country
    if not check_country_access(restaurant.country):
        flask.flash("You do not have permission to view this restaurant.", "error")
        return flask.redirect(flask.url_for("restaurant.list_restaurants"))

    menu_items = (
        db.session.query(MenuItem)
        .filter_by(restaurant_id=restaurant_id)
        .order_by(MenuItem.name)
        .all()
    )

    return flask.render_template(
        "restaurant/view.html", restaurant=restaurant, items=menu_items
    )
