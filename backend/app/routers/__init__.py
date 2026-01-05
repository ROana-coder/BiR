"""API routers package."""

from app.routers.search import router as search_router
from app.routers.graph import router as graph_router
from app.routers.geo import router as geo_router
from app.routers.recommendations import router as recommendations_router

__all__ = [
    "search_router",
    "graph_router",
    "geo_router",
    "recommendations_router",
]
