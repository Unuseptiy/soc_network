from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, exc
from uuid import UUID

from soc_network.db.models import User
from soc_network.schemas import RegistrationForm
from . import exceptions as custom_exc


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, potential_user: RegistrationForm) -> str:
        new_user = User(**potential_user.dict())
        self.session.add(new_user)
        try:
            await self.session.commit()
        except exc.IntegrityError:
            raise custom_exc.DbError('Username/email already exists.')
        await self.session.refresh(new_user)
        return new_user.id

    async def get(self, user_id: UUID):
        get_user_query = select(User).where(User.id == user_id)
        user_from_db = await self.session.scalar(get_user_query)
        if user_from_db is None:
            return None
        return user_from_db

    # todo: refactor
    # todo: add tests
    async def get_by_username(self, username: str):
        get_user_query = select(User).where(User.username == username)
        user_from_db = await self.session.scalar(get_user_query)
        if user_from_db is None:
            return None
        return user_from_db

    async def delete(self, user_id: UUID):
        delete_user_query = delete(User).where(User.id == user_id)
        await self.session.execute(delete_user_query)
        await self.session.commit()
