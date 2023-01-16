from uuid import UUID
from pydantic import BaseModel, constr


class Post(BaseModel):
    # id: UUID
    body: constr(min_length=1)
    author_id: UUID

    class Config:
        orm_mode = True
