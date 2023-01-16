from datetime import timedelta
from fastapi import APIRouter, Body, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from soc_network.config import get_settings
from soc_network.db.connection import get_session
from soc_network.db.models import User
from soc_network.schemas import RegistrationForm, RegistrationSuccess, Token
from soc_network.schemas import User as UserSchema
from soc_network.services.user import service
from soc_network.services import exceptions as serv_exc
from soc_network.repositories import UserRepository


api_router = APIRouter(
    prefix="/user",
    tags=["User"],
)


@api_router.post(
    "/authentication",
    status_code=status.HTTP_200_OK,
    response_model=Token,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Incorrect username or password."
        },
    }
)
async def authentication(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    user_repo = UserRepository(session)
    user = await service.authenticate_user(user_repo, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=get_settings().ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = service.create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@api_router.post(
    "/registration",
    status_code=status.HTTP_201_CREATED,
    response_model=RegistrationSuccess,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad parameters for registration.",
        },
    },
)
async def registration(
    registration_form: RegistrationForm = Body(...),
    session: AsyncSession = Depends(get_session),
):
    user_repo = UserRepository(session)
    is_success, message = await service.register_user(user_repo, registration_form)
    if is_success:
        return {"message": message}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=message,
    )


@api_router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=UserSchema,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Could not validate credentials.",
        },
    },
)
async def get_me(
    current_user: User = Depends(service.get_current_user),
):
    return UserSchema.from_orm(current_user)


@api_router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Could not validate credentials.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "No such user."
        },
    },
)
async def delete_user(
    current_user: User = Depends(service.get_current_user),
    session: AsyncSession = Depends(get_session),
):
    user_repo = UserRepository(session)
    try:
        await service.delete_user(user_repo, current_user.id)
    except serv_exc.NoUserError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'No user {current_user.username}')
