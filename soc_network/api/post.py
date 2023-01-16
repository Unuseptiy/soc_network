import uuid
from uuid import UUID
from fastapi import APIRouter, Body, Query, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from soc_network.db.connection import get_session
from soc_network.db.models import User
from soc_network.schemas import Post as PostSchema, PostActionEnum
from soc_network.services.post import service
from soc_network.services.user import service as user_service
from soc_network.services import exceptions as serv_exc
from soc_network.repositories import PostRepository, UserRepository, PostActionRepository


api_router = APIRouter(
    prefix="/post",
    tags=["Post"],
)


@api_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "User not found."
        }
    }
)
async def create_post(
        body: str = Body(..., min_length=1),
        current_user: User = Depends(user_service.get_current_user),
        session: AsyncSession = Depends(get_session),
):
    """
    Creates post in system.
    - input:
        body: post body
    - output:
        post_id: post id

    """
    post_repo = PostRepository(session)
    post = PostSchema(body=body, author_id=current_user.id)
    try:
        post_id = await service.create_post(post=post, post_repo=post_repo)
        return {'post_id': post_id}
    except serv_exc.NoUserError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No user {current_user.username}')


@api_router.put(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    # response_model=PostSchema,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Resource update successfully."
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Could not validate credentials.",
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "User have not permissions."
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Resource not found.",
        },
    },
)
async def update_post(
        post_id: uuid.UUID = Query(...),
        new_body: str = Body(..., min_length=1),
        current_user: User = Depends(user_service.get_current_user),
        session: AsyncSession = Depends(get_session),
):
    post_repo = PostRepository(session)
    try:
        await service.update_post(post_id=post_id, new_body=new_body, user=current_user, post_repo=post_repo)
        return
    except serv_exc.NotPermissionsError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f'The user `{current_user.username}` can not edit the post `{post_id}`')
    except serv_exc.NoPostError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Post {post_id} not found.')


@api_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=PostSchema,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Could not validate credentials.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Resource not found.",
        },
    },
)
async def get_post(
        post_id: uuid.UUID = Query(...),
        current_user: User = Depends(user_service.get_current_user),
        session: AsyncSession = Depends(get_session),
):
    """
    Gets post
    - input:
        - post_id: post id
    - output:
        body: post body
        author: post author
    """
    post_repo = PostRepository(session)
    post = await service.get_post(post_id=post_id, post_repo=post_repo)
    if post:
        return PostSchema.from_orm(post)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail=f'Post {post_id} not found.')


@api_router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Could not validate credentials.",
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "User have not permissions."
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "That post not found."
        },
    },
)
async def delete_post(
        post_id: uuid.UUID,
        current_user: User = Depends(user_service.get_current_user),
        session: AsyncSession = Depends(get_session),
):
    post_repo = PostRepository(session)
    user_repo = UserRepository(session)
    post_act_repo = PostActionRepository(session)
    try:
        await service.delete_post(
            post_id=post_id,
            user=current_user,
            post_repo=post_repo,
            user_repo=user_repo,
            post_act_repo=post_act_repo,
        )
    except serv_exc.NotPermissionsError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f'The user `{current_user.username}` can not delete the post `{post_id}`')
    except serv_exc.NoUserError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'User {current_user.username} not found')
    except serv_exc.NoPostError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Post {post_id} not found')


@api_router.post(
    "/{action}",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad parameters for registration.",
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "User have not permissions.",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Resources not found.",
        },
        status.HTTP_409_CONFLICT: {
            "description": "Resource already exists.",
        },
    },
)
async def rate_post(
        action: PostActionEnum,
        post_id: UUID = Query(...),
        current_user: User = Depends(user_service.get_current_user),
        session: AsyncSession = Depends(get_session),
):
    """
    Adds like/dislike to post.
    - input:
        - post_id: post id
    - output:
        - empty
    """
    post_repo = PostRepository(session)
    user_repo = UserRepository(session)
    post_act_repo = PostActionRepository(session)
    try:
        await service.rate_post(
            post_id=post_id,
            user=current_user,
            action=action,
            post_repo=post_repo,
            user_repo=user_repo,
            post_act_repo=post_act_repo,
        )
        return {'message': 'Successful assessment!'}
    except serv_exc.NotPermissionsError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f'The user `{current_user.username}` can not rate the post `{post_id}`')
    except serv_exc.NoUserError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No user `{current_user.username}`')
    except serv_exc.NoPostError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'No post `{post_id}`')
    except serv_exc.ActionDuplicateError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f'The rate {action} to the post {post_id} from the user {current_user.username} '
                                   f'already exist')


@api_router.delete(
    "/{action}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Could not validate credentials.",
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "User have not permissions."
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "That post not found."
        },
    },
)
async def delete_post_action(
        action: PostActionEnum,
        post_id: UUID = Query(...),
        current_user: User = Depends(user_service.get_current_user),
        session: AsyncSession = Depends(get_session),
):
    post_repo = PostRepository(session)
    user_repo = UserRepository(session)
    post_act_repo = PostActionRepository(session)
    try:
        await service.delete_post_rate(
            post_id=post_id,
            user=current_user,
            action=action,
            post_repo=post_repo,
            user_repo=user_repo,
            post_act_repo=post_act_repo,
        )
    except serv_exc.NotPermissionsError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'There is no action {action} on the post {post_id} from the '
                                   f'user {current_user.username}')
    except serv_exc.NoUserError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'User {current_user.username} not found')
    except serv_exc.NoPostError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Post {post_id} not found')