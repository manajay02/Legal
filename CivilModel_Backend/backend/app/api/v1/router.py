"""
Main API v1 router.
Combines all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import process, retrieve, upload

api_router = APIRouter()

# Include all endpoint routers
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
