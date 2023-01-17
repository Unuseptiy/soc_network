from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, exc
from uuid import UUID

from soc_network.db.models import PostAction
from . import exceptions as custom_exc


class PostActionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, user_id: UUID, post_id: UUID, action: str):
        new_post_action = PostAction(user_id=user_id, post_id=post_id, action=action)
        self.session.add(new_post_action)
        try:
            await self.session.commit()
        except exc.IntegrityError:
            raise custom_exc.DbError('This post action already exists.')
        except OSError:
            raise custom_exc.DbUnavailable(code=500, message='Database unavailable.')
        await self.session.refresh(new_post_action)

    async def list_by(self, **kwargs):
        list_post_action_query = select(PostAction)
        if 'post_id' in kwargs:
            list_post_action_query = list_post_action_query.where(PostAction.post_id == kwargs['post_id'])
        if 'user_id' in kwargs:
            list_post_action_query = list_post_action_query.where(PostAction.user_id == kwargs['user_id'])
        if 'action' in kwargs:
            list_post_action_query = list_post_action_query.where(PostAction.action == kwargs['action'])
        try:
            post_actions_from_db = await self.session.scalars(list_post_action_query)
            if post_actions_from_db is None:
                return None
            return post_actions_from_db
        except OSError:
            raise custom_exc.DbUnavailable(code=500, message='Database unavailable.')

    async def delete(self, user_id: UUID, post_id: UUID, action: str):
        delete_post_act_query = delete(PostAction).where(
            and_(
                PostAction.user_id == user_id,
                PostAction.post_id == post_id,
                PostAction.action == action,
            )
        )
        await self.session.execute(delete_post_act_query)
        try:
            await self.session.commit()
        except OSError:
            raise custom_exc.DbUnavailable(code=500, message='Database unavailable.')

    async def delete_by_post_user_id(self, post_id: UUID, user_id: UUID):
        delete_post_act_query = delete(PostAction).where(
            and_(
                PostAction.user_id == user_id,
                PostAction.post_id == post_id,
            )
        )
        await self.session.execute(delete_post_act_query)
        try:
            await self.session.commit()
        except OSError:
            raise custom_exc.DbUnavailable(code=500, message='Database unavailable.')
