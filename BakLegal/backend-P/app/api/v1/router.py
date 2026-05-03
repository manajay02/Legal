"""
Main API v1 router.
Combines all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, process, retrieve, search, upload

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    auth.router,
    tags=["auth"]
)

api_router.include_router(
    upload.router,
    tags=["upload"]
)

api_router.include_router(
    process.router,
    tags=["process"]
)

api_router.include_router(
    retrieve.router,
    tags=["documents"]
)

api_router.include_router(
    search.router,
    tags=["search"]
)
