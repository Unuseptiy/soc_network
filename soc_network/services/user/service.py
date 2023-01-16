import uuid
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from soc_network.repositories import UserRepository
from soc_network.schemas import RegistrationForm

from soc_network.config import get_settings
from soc_network.db.connection import get_session
from soc_network.db.models import User
from soc_network.schemas import TokenData
from soc_network.repositories import exceptions as db_exc
from soc_network.services import exceptions as serv_exc


async def register_user(
        user_repo: UserRepository,
        user: RegistrationForm,
):
    try:
        await user_repo.add(user)
    except db_exc.DbError:
        return False, "Username already exists."
    return True, "Successful registration!"


async def authenticate_user(
    user_repo: UserRepository,
    username: str,
    password: str,
):
    user = await user_repo.get_by_username(username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
):
    settings = get_settings()
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_password(
    plain_password: str,
    hashed_password: str,
):
    pwd_context = get_settings().PWD_CONTEXT
    return pwd_context.verify(plain_password, hashed_password)


async def get_current_user(
    session: AsyncSession = Depends(get_session),
    token: str = Depends(get_settings().OAUTH2_SCHEME),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_repo = UserRepository(session)
    try:
        payload = jwt.decode(token, get_settings().SECRET_KEY, algorithms=[get_settings().ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = await user_repo.get_by_username(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def delete_user(user_repo: UserRepository, user_id: uuid.UUID):
    user = await user_repo.get(user_id=user_id)
    if not user:
        raise serv_exc.NoUserError('No such user.')
    await user_repo.delete(user_id=user_id)
