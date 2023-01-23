from datetime import timedelta
from fastapi import APIRouter, Body, Depends, HTTPException, Response, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from soc_network.config import get_settings
from soc_network.db.connection import get_session
from soc_network.db.models import User
from soc_network.schemas import RegistrationForm, RegistrationSuccess, Token
from soc_network.schemas import User as UserSchema
from soc_network.services.user import service
from soc_network.services import exceptions as serv_exc
from soc_network.repositories import UserRepository

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler(f"{__name__}.log")
formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")

handler.setFormatter(formatter)
logger.addHandler(handler)


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
        request: Request,
        form_data: OAuth2PasswordRequestForm = Depends(),
        session: AsyncSession = Depends(get_session),
):
    """
    Authenticates user.
    - input:
        - username
        - password
    - output:
        - access_token
        - token_type
    """
    user_repo = UserRepository(session)
    user = await service.authenticate_user(user_repo, form_data.username, form_data.password)
    logger.info(
        "method: %(method)s, client: %(client)s, path: %(path)s, params: {username: %(username)s}, "
        "status_code: %(status)s" %
        {'method': request.method, 'client': request.client.host, 'path': request.url.path,
         'username': form_data.username,
         'status': 200 if user else 401})
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
        status.HTTP_409_CONFLICT: {
            "description": "Received username and/or email already taken.",
        },
        status.HTTP_424_FAILED_DEPENDENCY: {
            "description": "Received email verification failed."
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Server can not verify received email."
        },
    },
)
async def registration(
        request: Request,
        background_tasks: BackgroundTasks,
        registration_form: RegistrationForm = Body(...),
        session: AsyncSession = Depends(get_session),
):
    """
    Registers user.
    - input:
        - username
        - password
        - email
    - output:
        - message: operation status message.
    """
    user_repo = UserRepository(session)
    try:
        await service.register_user(user_repo, registration_form)
        background_tasks.add_task(service.get_additional_user_data, registration_form, user_repo)
        logger.info(
            "method: %(method)s, client: %(client)s, path: %(path)s, params: {username: %(username)s, email: %(email)s},"
            " status_code: %(status_code)s" %
            {'method': request.method,
             'client': request.client.host,
             'path': request.url.path,
             'username': registration_form.username,
             'email': registration_form.email,
             'status_code': 201})
        return {"message": "Successful registration!"}
    except serv_exc.UserAttrsAlreadyExist:
        logger.info(
            "method: %(method)s, client: %(client)s, path: %(path)s, params: {username: %(username)s, email: %(email)s},"
            " status_code: %(status_code)s" %
            {'method': request.method,
             'client': request.client.host,
             'path': request.url.path,
             'username': registration_form.username,
             'email': registration_form.email,
             'status_code': 409})
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username and/or email already taken.")
    except serv_exc.UnVerifiedEmailError:
        logger.info(
            "method: %(method)s, client: %(client)s, path: %(path)s, params: {username: %(username)s, email: %(email)s},"
            " status_code: %(status_code)s" %
            {'method': request.method,
             'client': request.client.host,
             'path': request.url.path,
             'username': registration_form.username,
             'email': registration_form.email,
             'status_code': 424})
        raise HTTPException(status_code=status.HTTP_424_FAILED_DEPENDENCY, detail="Can not verify current email."
                                                                                  "Please enter another email.")
    except serv_exc.VerifierTimeoutError:
        logger.error(
            "method: %(method)s, client: %(client)s, path: %(path)s, params: {username: %(username)s, email: %(email)s},"
            " status_code: %(status_code)s" %
            {'method': request.method,
             'client': request.client.host,
             'path': request.url.path,
             'username': registration_form.username,
             'email': registration_form.email,
             'status_code': 503})
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Cannot verify email.")
    except serv_exc.VerifierUnavailable:
        logger.error("method: %(method)s, client: %(client)s, path: %(path)s, params: {username: %(username)s, "
                     "email: %(email)s}, status_code: %(status_code)s" %
                     {'method': request.method,
                      'client': request.client.host,
                      'path': request.url.path,
                      'username': registration_form.username,
                      'email': registration_form.email,
                      'status_code': 503})
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Cannot verify email.")


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
        request: Request,
        current_user: User = Depends(service.get_current_user),
):
    """
    Returns current user.
    - input:
        - empty
    - output:
        - UserSchema: user attributes.
    """
    logger.info("method: %(method)s, client: %(client)s, path: %(path)s, params: {username: %(username)s}, "
                "status_code: %(status_code)s" %
                {'method': request.method,
                 'client': request.client.host,
                 'path': request.url.path,
                 'username': current_user.username,
                 'status_code': 200 if current_user else 401})
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
        request: Request,
        current_user: User = Depends(service.get_current_user),
        session: AsyncSession = Depends(get_session),
):
    """
    Deletes current user.
    - input:
        - empty
    - output:
        - empty
    """
    user_repo = UserRepository(session)
    try:
        await service.delete_user(user_repo, current_user.id)
        logger.info("method: %(method)s, client: %(client)s, path: %(path)s, params: {username: %(username)s}, "
                    "status_code: %(status_code)s" %
                    {'method': request.method,
                     'client': request.client.host,
                     'path': request.url.path,
                     'username': current_user.username,
                     'status_code': 204})
    except serv_exc.NoUserError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'No user {current_user.username}')
