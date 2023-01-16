from enum import Enum
from pydantic import BaseModel

from uuid import UUID


class PostActionEnum(str, Enum):
    LIKE = "LIKE"
    DISLIKE = "DISLIKE"


class PostAction(BaseModel):
    user_id: UUID
    post_id: UUID
    action: PostActionEnum

    class Config:
        orm_mode = True
        use_enum_values = True


class ActionResult(BaseModel):
    message: str
