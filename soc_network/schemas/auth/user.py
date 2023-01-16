from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    dt_created: datetime
    dt_updated: datetime

    class Config:
        orm_mode = True
