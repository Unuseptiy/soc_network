import uuid
import pytest

from soc_network.repositories import UserRepository, PostRepository, PostActionRepository, exceptions as db_exc
from soc_network.db.connection import get_session_for_test
from soc_network.schemas import RegistrationForm, Post as PostSchema


pytestmark = pytest.mark.asyncio


class TestUserRepo:
    async def test_add_user(self):
        sess = await get_session_for_test()
        user_repo = UserRepository(sess)
        potential_user = RegistrationForm(username='johndoe', password='hackme', email='johndoe@mail.com')
        new_user_id = await user_repo.add(potential_user)

        user_in_db = await user_repo.get(user_id=new_user_id)
        assert potential_user.username == user_in_db.username
        assert potential_user.email == user_in_db.email

        await user_repo.delete(user_id=new_user_id)
        await sess.close()


class TestPostRepo:
    async def test_add_post(self):
        sess = await get_session_for_test()
        user_repo = UserRepository(sess)
        potential_user = RegistrationForm(username='johndoe', password='hackme', email='johndoe@mail.com')
        new_user_id = await user_repo.add(potential_user)
        user_in_db = await user_repo.get(user_id=new_user_id)

        post_repo = PostRepository(sess)
        potential_post = PostSchema(body="First post.", author_id=user_in_db.id)
        new_post_id = await post_repo.add(post=potential_post)

        post_in_db = await post_repo.get(post_id=new_post_id)

        assert potential_post.body == post_in_db.body
        # assert potential_user.email == user_in_db.email

        await post_repo.delete(post_id=new_post_id)
        await user_repo.delete(user_id=new_user_id)
        await sess.close()

    async def test_delete_not_existent_post(self):
        sess = await get_session_for_test()
        post_repo = PostRepository(sess)

        await post_repo.delete(post_id='7eb15644-40f8-4f1b-9f72-ab84d5b0be0b')
        await sess.close()

    async def test_add_post_non_exist_user(self):
        sess = await get_session_for_test()
        post_repo = PostRepository(sess)
        potential_post = PostSchema(body="First post.", author_id=uuid.uuid4())
        with pytest.raises(db_exc.DbError):
            new_post_id = await post_repo.add(post=potential_post)
        await sess.close()


class TestPostActRepo:
    @pytest.fixture()
    async def create_users_and_posts(self):
        sess = await get_session_for_test()

        user_repo = UserRepository(sess)
        users = [
            ['johndoe', 'hackme', 'johndoe@mail.ru'],
            ['foo', 'pass', 'foo@yandex.ru'],
            ['kek', 'password', 'kek@gmail.com'],
        ]
        for i, user in enumerate(users):
            name, passw, email = user
            potential_user = RegistrationForm(username=name, password=passw, email=email)
            new_user_id = await user_repo.add(potential_user)
            users[i].append(new_user_id)
            # user_in_db = await user_repo.get(user_id=new_user_id)

        post_repo = PostRepository(sess)
        posts = [
            ['Johndoe first post.', users[0][-1]],
            ['Johndoe sec post.', users[0][-1]],
            ['Johndoe news post.', users[0][-1]],
            ['lol', users[-1][-1]],
            ['rofl', users[-1][-1]],
        ]
        for i, post in enumerate(posts):
            body, user_id = post
            potential_post = PostSchema(body=body, author_id=user_id)
            new_post_id = await post_repo.add(post=potential_post)
            posts[i].append(new_post_id)

        yield [i[-1] for i in users], [i[-1] for i in posts]

        for i in posts:
            await post_repo.delete(post_id=i[-1])
        for i in users:
            await user_repo.delete(user_id=i[-1])

        await sess.close()

    async def test_add_post_act(self):
        sess = await get_session_for_test()
        ##### TEST SETUP START #####
        user_repo = UserRepository(sess)
        users = [
            ['johndoe', 'hackme', 'johndoe@mail.ru'],
            ['foo', 'pass', 'foo@yandex.ru'],
            ['kek', 'password', 'kek@gmail.com'],
        ]
        for i, user in enumerate(users):
            name, passw, email = user
            potential_user = RegistrationForm(username=name, password=passw, email=email)
            new_user_id = await user_repo.add(potential_user)
            users[i].append(new_user_id)
            # user_in_db = await user_repo.get(user_id=new_user_id)

        post_repo = PostRepository(sess)
        posts = [
            ['Johndoe first post.', users[0][-1]],
            ['Johndoe sec post.', users[0][-1]],
            ['Johndoe news post.', users[0][-1]],
            ['lol', users[-1][-1]],
            ['rofl', users[-1][-1]],
        ]
        for i, post in enumerate(posts):
            body, user_id = post
            potential_post = PostSchema(body=body, author_id=user_id)
            new_post_id = await post_repo.add(post=potential_post)
            posts[i].append(new_post_id)

        users_ids = [i[-1] for i in users]
        posts_ids = [i[-1] for i in posts]

        ##### TEST SETUP END #####

        post_act_repo = PostActionRepository(sess)

        await post_act_repo.add(users_ids[1], posts_ids[0], action='like'.upper())
        await post_act_repo.add(users_ids[2], posts_ids[0], action='dislike'.upper())
        await post_act_repo.add(users_ids[1], posts_ids[-1], action='like'.upper())
        await post_act_repo.add(users_ids[1], posts_ids[-2], action='like'.upper())

        acts_list = await post_act_repo.list_by(user_id=users_ids[2])
        assert acts_list[0].post_id == posts_ids[0]

        await post_act_repo.delete(users_ids[1], posts_ids[0], action='like'.upper())
        await post_act_repo.delete(users_ids[2], posts_ids[0], action='dislike'.upper())
        await post_act_repo.delete(users_ids[1], posts_ids[-1], action='like'.upper())
        await post_act_repo.delete(users_ids[1], posts_ids[-2], action='like'.upper())

        #### TEST SETDOWN START ####
        for i in posts:
            await post_repo.delete(post_id=i[-1])
        for i in users:
            await user_repo.delete(user_id=i[-1])
        #### TEST SETDOWN END ####

        await sess.close()

    async def test_add_post_act_not_exist_fk(self):
        sess = await get_session_for_test()
        post_act_repo = PostActionRepository(sess)
        with pytest.raises(db_exc.DbError):
            await post_act_repo.add(uuid.uuid4(), uuid.uuid4(), action='like'.upper())
        await sess.close()
