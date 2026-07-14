"""
API v1 router initialization.
"""

from fastapi import APIRouter

from app.api.v1 import auth, meetings, health

api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(meetings.router, prefix="/meetings", tags=["meetings"])
api_router.include_router(health.router, prefix="/health", tags=["health"])

__all__ = ["api_router"]