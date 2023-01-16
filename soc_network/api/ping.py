from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from soc_network.db.connection import get_session
from soc_network.schemas import PingResponse
from soc_network.services.health_check import health_check_db


api_router = APIRouter(
    prefix="/health_check",
    tags=["Application Health"],
)


@api_router.get(
    "/ping_application",
    response_model=PingResponse,
    status_code=status.HTTP_200_OK,
)
async def ping_application():
    return {"message": "Application worked!"}


@api_router.get(
    "/ping_database",
    response_model=PingResponse,
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Database isn't working."}},
)
async def ping_database(
    session: AsyncSession = Depends(get_session),
):
    if await health_check_db(session):
        return {"message": "Database worked!"}
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Database isn't working",
    )
