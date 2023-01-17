from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from uvicorn import run

from soc_network.config import DefaultSettings, get_settings
from soc_network.db.connection import SessionManager
from soc_network.services.common import get_hostname
from soc_network.api import list_of_routes
from soc_network.repositories.exceptions import DbUnavailable


def bind_routes(application: FastAPI, setting: DefaultSettings) -> None:
    """
    Bind all routes to application.
    """
    for route in list_of_routes:
        application.include_router(route, prefix=setting.PATH_PREFIX)


def init_database() -> None:
    """
    Creates a reusable database connection.
    Check before launching the application that the database is available to it.
    """
    SessionManager()


def get_app() -> FastAPI:
    """
    Creates application and all dependable objects.
    """
    description = "Сервис, реализующий часть функционала социальной сети."

    tags_metadata = [
        {
            "name": "Application Health",
            "description": "API health check.",
        },
    ]

    application = FastAPI(
        title="Social network.",
        description=description,
        docs_url="/docs",
        openapi_url="/openapi",
        version="0.1.0",
        openapi_tags=tags_metadata,
    )

    @application.exception_handler(DbUnavailable)
    async def api_exception_handler(request: Request, exc: DbUnavailable):
        return JSONResponse(
            status_code=exc.code,
            content={"code": exc.code, "message": exc.message}
        )

    settings = get_settings()
    bind_routes(application, settings)
    init_database()
    application.state.settings = settings
    return application


app = get_app()

if __name__ == "__main__":
    settings_for_application = get_settings()
    run(
        "soc_network.__main__:app",
        host=get_hostname(settings_for_application.APP_HOST),
        port=settings_for_application.APP_PORT,
        reload=True,
        reload_dirs=["soc_network", "tests"],
        log_level="debug",
    )
