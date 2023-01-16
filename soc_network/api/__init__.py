from soc_network.api.auth import api_router as auth_router
from soc_network.api.post import api_router as bookmarks_router
from soc_network.api.ping import api_router as application_health_router


list_of_routes = [
    application_health_router,
    auth_router,
    bookmarks_router,
]


__all__ = [
    "list_of_routes",
]
