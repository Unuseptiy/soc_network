from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import TEXT

from soc_network.db import DeclarativeBase


class PostAction(DeclarativeBase):
    __tablename__ = "post_action"

    user_id = Column(
        "user_id",
        ForeignKey("user.id"),
        primary_key=True,
        doc="Identifier of user who put the like.",
    )
    post_id = Column(
        "post_id",
        ForeignKey("post.id"),
        primary_key=True,
        doc="Identifier of the post user liked.",
    )
    action = Column(
        "action",
        TEXT,
        primary_key=True,
        doc="Describes the user's action in relation to the publication.",
    )
