from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import TEXT

from .base import BaseTable


class User(BaseTable):
    __tablename__ = "user"

    username = Column(
        "username",
        TEXT,
        nullable=False,
        unique=True,
        index=True,
        doc="Username for authentication.",
    )
    password = Column(
        "password",
        TEXT,
        nullable=False,
        index=True,
        doc="Hashed password.",
    )
    email = Column(
        "email",
        # todo: заменить на строку
        TEXT,
        nullable=True,
        unique=True,
        doc="User email.",
    )
    data = Column(
        "data",
        TEXT,
        nullable=True,
        doc="Additional user data from Clearbit in json.",
    )
