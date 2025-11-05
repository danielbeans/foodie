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
    price_unit = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    restaurant = relationship("Restaurant", back_populates="menu_items")

    def __repr__(self):
        return f"<MenuItem {self.name} (${self.price})>"
