import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import relationship

from foodie.db import db


class User(db.Model):
    """User model with role-based access control."""

    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(
        String,
        CheckConstraint("role IN ('ADMIN', 'MANAGER', 'MEMBER')"),
        nullable=False,
    )
    country = Column(
        String, CheckConstraint("country IN ('India', 'America')"), nullable=False
    )
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    orders = relationship("Order", back_populates="user")

    def __repr__(self):
        return f"<User {self.username} ({self.role}, {self.country})>"


class Restaurant(db.Model):
    """Restaurant model with country assignment."""

    __tablename__ = "restaurant"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    country = Column(
        String, CheckConstraint("country IN ('India', 'America')"), nullable=False
    )
    address = Column(String)
    phone = Column(String)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    menu_items = relationship("MenuItem", back_populates="restaurant")
    orders = relationship("Order", back_populates="restaurant")

    def __repr__(self):
        return f"<Restaurant {self.name} ({self.country})>"


class MenuItem(db.Model):
    """Menu item model."""

    __tablename__ = "menu_item"

    id = Column(Integer, primary_key=True)
    restaurant_id = Column(Integer, ForeignKey("restaurant.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    restaurant = relationship("Restaurant", back_populates="menu_items")
    order_items = relationship("OrderItem", back_populates="menu_item")

    def __repr__(self):
        return f"<MenuItem {self.name} (${self.price})>"


class Order(db.Model):
    """Order model"""

    __tablename__ = "order"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurant.id"), nullable=False)
    status = Column(
        String,
        CheckConstraint("status IN ('DRAFT', 'PLACED', 'CANCELLED', 'COMPLETED')"),
        nullable=False,
        default="DRAFT",
    )
    total_amount = Column(Float, nullable=False, default=0.0)
    notes = Column(String)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    placed_at = Column(DateTime)
    cancelled_at = Column(DateTime)

    user = relationship("User", back_populates="orders")
    restaurant = relationship("Restaurant", back_populates="orders")
    order_items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Order #{self.id} ({self.status}) - ${self.total_amount}>"


class OrderItem(db.Model):
    """Order item model"""

    __tablename__ = "order_item"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("order.id"), nullable=False)
    menu_item_id = Column(Integer, ForeignKey("menu_item.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    notes = Column(String)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    order = relationship("Order", back_populates="order_items")
    menu_item = relationship("MenuItem", back_populates="order_items")

    def __repr__(self):
        return f"<OrderItem {self.quantity}x {self.unit_price} = ${self.subtotal}>"
