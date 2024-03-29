from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import TEXT

from .base import BaseTable


class Post(BaseTable):
    __tablename__ = "post"

    body = Column(
        "body",
        TEXT,
        nullable=False,
        doc="Post body.",
    )
    author_id = Column(
        "author_id",
        ForeignKey('user.id'),
        nullable=False,
        doc="Post author.",
    )
