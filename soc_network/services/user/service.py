import uuid
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
import aiohttp
import asyncio
import logging

from soc_network.repositories import UserRepository
from soc_network.schemas import RegistrationForm
from soc_network.config import get_settings
from soc_network.db.connection import get_session
from soc_network.db.models import User
from soc_network.schemas import TokenData
from soc_network.repositories import exceptions as db_exc
from soc_network.services import exceptions as serv_exc

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

handler = logging.FileHandler(f"{__name__}.log")
formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")

handler.setFormatter(formatter)
logger.addHandler(handler)


async def register_user(
        user_repo: UserRepository,
        user: RegistrationForm,
):
    haunter_api_key = get_settings().HUNTER_API_KEY
    hunter_verify_url = "https://api.hunter.io/v2/email-verifier"
    query_params = {"email": user.email, "api_key": haunter_api_key}
    valid_body_statuses = {"valid", "webmail"}
    try:
        timeout = aiohttp.ClientTimeout(total=23)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(hunter_verify_url, params=query_params) as resp:
                verify_status_code = resp.status
                resp_json = await resp.json()
                verify_body_status = resp_json["data"]["status"]
    except asyncio.exceptions.TimeoutError:
        logger.error("Hunter.io timeout error")
        raise serv_exc.VerifierTimeoutError("Verify timeout.")
    except aiohttp.ClientConnectorError:
        logger.error("Hunter.io is unavailable.")
        raise serv_exc.VerifierUnavailable("Verifier is unavailable.")
    if verify_status_code != 200 or verify_body_status not in valid_body_statuses:
        logger.info(f"Email {user.email} is not verified. Verifier status is {verify_body_status}")
        raise serv_exc.UnVerifiedEmailError("Email not verified.")
    logger.info(f"Email {user.email} is verified. Verifier status is {verify_body_status}")

    try:
        await user_repo.add(user)
    except db_exc.DbError:
        raise serv_exc.UserAttrsAlreadyExist("Username and/or email already taken.")


async def get_additional_user_data(user: RegistrationForm, user_repo: UserRepository):
    """Add additional user data from Clearbit to User in db."""

    clearbit_email_find_url = "https://person.clearbit.com/v2/people/find"
    query_params = {'email': user.email}
    headers = {'Authorization': f'Bearer {get_settings().CLEARBIT_API_KEY}'}
    try:
        timeout = aiohttp.ClientTimeout(total=23)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(clearbit_email_find_url, params=query_params, headers=headers) as resp:
                find_status_code = resp.status
                resp_json = await resp.json()
    except asyncio.exceptions.TimeoutError:
        logger.error("Clearbit timeout error")
    except aiohttp.ClientConnectorError:
        logger.error("Clearbit is unavailable.")
    if find_status_code == 200:
        try:
            await user_repo.update_by_email(email=user.email, data=str(resp_json))
        except db_exc.DbError:
            ...
    else:
        # retry if 202
        # handle other status_codes
        logger.info(f"Additional data not received, clearbit response status code {find_status_code}")
        ...


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
        logger.warning(f"can not decode JWT token: {token}")
        raise credentials_exception
    user = await user_repo.get_by_username(username=token_data.username)
    if user is None:
        logger.warning(f"can not find user {user} from JWT token: {token}")
        raise credentials_exception
    return user


async def delete_user(user_repo: UserRepository, user_id: uuid.UUID):
    user = await user_repo.get(user_id=user_id)
    if not user:
        raise serv_exc.NoUserError('No such user.')
    await user_repo.delete(user_id=user_id)
