from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, exc
from uuid import UUID

from soc_network.db.models import Post
from soc_network.schemas import Post as PostSchema
from . import exceptions as custom_exc


# todo: посмотреть как ведет себя при добавлении текста превышающего допустимую в БД
class PostRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, post: PostSchema):
        new_post = Post(body=post.body, author_id=post.author_id)
        self.session.add(new_post)
        # todo: протестить - какая ошибка возвращается при отстутствующем в БД author_id
        try:
            await self.session.commit()
        except exc.IntegrityError:
            raise custom_exc.DbError('No user error.')
        await self.session.refresh(new_post)
        return new_post.id

    async def get(self, post_id: UUID):
        get_post_query = select(Post).where(Post.id == post_id)
        post_from_db = await self.session.scalar(get_post_query)
        if post_from_db is None:
            return None
        return post_from_db

    async def delete(self, post_id: UUID):
        delete_post_query = delete(Post).where(Post.id == post_id)
        await self.session.execute(delete_post_query)
        await self.session.commit()

    async def update(self, post_id: UUID, new_body: str):
        get_post_query = select(Post).where(Post.id == post_id)
        post_from_db = await self.session.scalar(get_post_query)
        if post_from_db is None:
            raise custom_exc.DbError(f'No such post id: {post_id}')
        post_from_db.body = new_body
        await self.session.commit()
