import json
from types import NoneType
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, exc
from uuid import UUID
import redis
from redis import Redis

from soc_network.db.models import PostAction
from soc_network.schemas import PostActionEnum, PostAction as PostActionSchema
from . import exceptions as custom_exc


class PostActionRepository:
    def __init__(self, session: AsyncSession, redis_sess: Redis = None):
        self.session = session
        try:
            redis_sess.ping()
            self.redis = redis_sess
        except redis.exceptions.ConnectionError:
            self.redis = None

    async def add(self, user_id: UUID, post_id: UUID, action: str):
        if self.redis:
            redis_key = str(post_id) + action
            self.redis.sadd(redis_key, PostActionSchema(user_id=user_id, post_id=post_id, action=action).json())

        new_post_action = PostAction(user_id=user_id, post_id=post_id, action=action)
        self.session.add(new_post_action)
        try:
            await self.session.commit()
        except exc.IntegrityError:
            raise custom_exc.DbError('This post action already exists.')
        except OSError:
            raise custom_exc.DbUnavailable(code=500, message='Database unavailable.')
        await self.session.refresh(new_post_action)

    async def list_by_post_id(self, post_id: UUID) -> list:
        post_acts = []
        if self.redis:
            redis_key_like = str(post_id) + PostActionEnum.LIKE.value
            redis_key_dislike = str(post_id) + PostActionEnum.DISLIKE.value
            redis_key_like_exist = self.cache_key_exists(redis_key_like)
            redis_key_dislike_exist = self.cache_key_exists(redis_key_dislike)
            if redis_key_like_exist:
                post_likes_from_redis = self.redis.smembers(redis_key_like)
                post_acts.extend(
                    [PostActionSchema(**json.loads(post_act_json)) for post_act_json in post_likes_from_redis])
            if redis_key_dislike_exist:
                post_dislikes_from_redis = self.redis.smembers(redis_key_dislike)
                post_acts.extend(
                    [PostActionSchema(**json.loads(post_act_json)) for post_act_json in post_dislikes_from_redis])
            if redis_key_like_exist and redis_key_dislike_exist:
                return post_acts

            # Upload missing keys from db, and add this keys to redis
            likes_from_db = []
            dislikes_from_db = []
            if not redis_key_like_exist:
                likes_from_db = await self.list_by_post_id_action(post_id=post_id, action=PostActionEnum.LIKE.value)
            if not redis_key_dislike_exist:
                dislikes_from_db = await self.list_by_post_id_action(post_id=post_id, action=PostActionEnum.DISLIKE.value)
            post_acts.extend(likes_from_db + dislikes_from_db)
            return post_acts
        else:
            list_post_action_query = select(PostAction).where(PostAction.post_id == post_id)
            try:
                post_actions_from_db = [post_act for post_act in await self.session.scalars(list_post_action_query)]
            except OSError:
                raise custom_exc.DbUnavailable(code=500, message='Database unavailable.')
            if len(post_actions_from_db) == 0:
                return []
            return post_actions_from_db

    async def list_by_post_id_action(self, post_id: UUID, action: str) -> list:
        post_acts = []
        if self.redis:
            redis_key_action = str(post_id) + action
            if self.cache_key_exists(redis_key_action):
                post_actions_from_redis = self.redis.smembers(redis_key_action)
                post_acts.extend(
                    [PostActionSchema(**json.loads(post_act_json)) for post_act_json in post_actions_from_redis])
            else:
                list_post_action_query = select(PostAction).where(PostAction.post_id == post_id,
                                                                  PostAction.action == action)
                try:
                    post_actions_from_db = [post_act for post_act in await self.session.scalars(list_post_action_query)]
                except OSError:
                    raise custom_exc.DbUnavailable(code=500, message='Database unavailable.')
                if len(post_actions_from_db) == 0:
                    # todo: add key to redis with empty set
                    return []

                self.redis.sadd(redis_key_action,
                                *[PostActionSchema.from_orm(post_act).json() for post_act in post_actions_from_db])
                return post_actions_from_db
        else:
            list_post_action_query = select(PostAction).where(PostAction.post_id == post_id,
                                                              PostAction.action == action)
            try:
                post_actions_from_db = [post_act for post_act in await self.session.scalars(list_post_action_query)]
            except OSError:
                raise custom_exc.DbUnavailable(code=500, message='Database unavailable.')
            return post_actions_from_db

    async def list_by_user_id(self, user_id: UUID) -> list:
        list_post_action_query = select(PostAction).where(PostAction.user_id == user_id)
        try:
            post_actions_from_db = [post_act for post_act in await self.session.scalars(list_post_action_query)]
        except OSError:
            raise custom_exc.DbUnavailable(code=500, message='Database unavailable.')
        if len(post_actions_from_db) == 0:
            return []
        return post_actions_from_db

    async def list_by_post_id_user_id(self, post_id: UUID, user_id: UUID) -> list:
        list_post_action_query = select(PostAction).where(PostAction.post_id == post_id, PostAction.user_id == user_id)
        try:
            post_actions_from_db = [post_act for post_act in await self.session.scalars(list_post_action_query)]
        except OSError:
            raise custom_exc.DbUnavailable(code=500, message='Database unavailable.')
        if len(post_actions_from_db) == 0:
            return []
        return post_actions_from_db

    async def delete(self, user_id: UUID, post_id: UUID, action: str):
        if self.redis:
            redis_key = str(post_id) + action
            self.redis.srem(redis_key, PostActionSchema(user_id=user_id, post_id=post_id, action=action).json())

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
        if self.redis:
            redis_key_like = str(post_id) + PostActionEnum.LIKE.value
            self.redis.srem(redis_key_like, PostActionSchema(user_id=user_id,
                                                             post_id=post_id,
                                                             action=PostActionEnum.LIKE.value).json())
            redis_key_dislike = str(post_id) + PostActionEnum.DISLIKE.value
            self.redis.srem(redis_key_dislike, PostActionSchema(user_id=user_id,
                                                                post_id=post_id,
                                                                action=PostActionEnum.DISLIKE.value).json())

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

    def cache_key_exists(self, key):
        try:
            return not isinstance(self.redis.get(key), NoneType)
        except redis.exceptions.ResponseError:
            return True
