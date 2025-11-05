import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
)

from foodie.db import db


class User(db.Model):
    """User model with role-based access control."""

    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    country = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username} ({self.role}, {self.country})>"
