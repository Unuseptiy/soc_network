from uuid import UUID

from soc_network.repositories import PostRepository, PostActionRepository, UserRepository
from soc_network.db.models import User
from soc_network.schemas import Post as PostSchema, PostActionEnum
from soc_network.services import exceptions as serv_exc
from soc_network.repositories import exceptions as db_exc


async def create_post(
        post: PostSchema,
        post_repo: PostRepository
):
    try:
        return await post_repo.add(post)
    except db_exc.DbError as e:
        raise serv_exc.NoUserError(e)


async def get_post(
        post_id: UUID,
        post_repo: PostRepository,
):
    return await post_repo.get(post_id=post_id)


async def update_post(
        post_id: UUID,
        new_body: str,
        user: User,
        post_repo: PostRepository,
):
    permissions = await have_permissions_to_edit_post(post_id, user, post_repo)
    if not permissions:
        raise serv_exc.NotPermissionsError(f'User {user.username} have not permissions to edit post {post_id}.')
    try:
        await post_repo.update(post_id=post_id, new_body=new_body)
    except db_exc.DbError as e:
        raise serv_exc.NoPostError(e)


async def delete_post(
        post_id: UUID,
        user: User,
        post_repo: PostRepository,
        user_repo: UserRepository,
        post_act_repo: PostActionRepository,
):
    user_from_db = await user_repo.get(user_id=user.id)
    if not user_from_db:
        raise serv_exc.NoUserError('No such user.')

    post = await post_repo.get(post_id=post_id)
    if not post:
        raise serv_exc.NoPostError(f'No such post id: {post_id}')

    permissions = await have_permissions_to_delete_post(post_id, user, post_repo)
    if not permissions:
        raise serv_exc.NotPermissionsError(f'User {user.username} have not permissions to delete post {post_id}.')

    # delete all actions that related to post
    post_acts = await post_act_repo.list_by(post_id=post_id)
    for post_act in post_acts:
        await post_act_repo.delete_by_post_user_id(post_id=post_id, user_id=post_act.user_id)

    await post_repo.delete(post_id=post_id)


async def rate_post(
        post_id: UUID,
        user: User,
        action: PostActionEnum,
        post_repo: PostRepository,
        user_repo: UserRepository,
        post_act_repo: PostActionRepository,
):
    user_from_db = await user_repo.get(user_id=user.id)
    if not user_from_db:
        raise serv_exc.NoUserError('No such user.')

    post_from_db = await post_repo.get(post_id=post_id)
    if not post_from_db:
        raise serv_exc.NoPostError('No such post.')

    permissions = await have_permissions_to_rate_post(post_id, user, post_repo)
    if not permissions:
        raise serv_exc.NotPermissionsError(f'User {user.username} have not permissions to evaluate post {post_id}.')

    # checking that there are no other actions from this user with this post
    post_acts = await post_act_repo.list_by(user_id=user.id, post_id=post_id)
    # if there is, then delete them all (like - is reverse action for dislike)
    action_duplicate_flag = False
    for post_act in post_acts:
        if post_act.action == action:
            action_duplicate_flag = True
            break
        else:
            await post_act_repo.delete(user_id=user.id, post_id=post_id, action=post_act.action)
    if action_duplicate_flag:
        raise serv_exc.ActionDuplicateError('This action duplicates existent action.')

    await post_act_repo.add(user_id=user.id, post_id=post_id, action=action)


async def delete_post_rate(
        post_id: UUID,
        user: User,
        action: PostActionEnum,
        post_repo: PostRepository,
        user_repo: UserRepository,
        post_act_repo: PostActionRepository,
):
    user_from_db = await user_repo.get(user_id=user.id)
    if not user_from_db:
        raise serv_exc.NoUserError('No such user.')

    post_from_db = await post_repo.get(post_id=post_id)
    if not post_from_db:
        raise serv_exc.NoPostError('No such post.')

    permissions = await have_permissions_to_delete_post_act(
        post_id=post_id,
        user=user,
        action=action,
        post_act_repo=post_act_repo
    )
    if not permissions:
        raise serv_exc.NotPermissionsError(f'There is not action {action} on the post {post_id} from the '
                                           f'user {user.username}')

    await post_act_repo.delete(user_id=user.id, post_id=post_id, action=action)


async def have_permissions_to_edit_post(
        post_id: UUID,
        user: User,
        post_repo: PostRepository,
):
    post = await post_repo.get(post_id=post_id)
    return post.author_id == user.id


async def have_permissions_to_delete_post(
        post_id: UUID,
        user: User,
        post_repo: PostRepository,
):
    post = await post_repo.get(post_id=post_id)
    return post.author_id == user.id


async def have_permissions_to_rate_post(
        post_id: UUID,
        user: User,
        post_repo: PostRepository,
):
    post = await post_repo.get(post_id=post_id)
    return post.author_id != user.id


async def have_permissions_to_delete_post_act(
        post_id: UUID,
        user: User,
        action: str,
        post_act_repo: PostActionRepository,
):
    post_acts = await post_act_repo.list_by(post_id=post_id, user_id=user.id)
    for post in post_acts:
        if post.action == action:
            return True
    return False
