"""API v1 module"""
from fastapi import APIRouter

from api.v1 import endpoints, auth, platform

# Combine all routers
router = APIRouter(prefix="/api/v1")

# Include routers
router.include_router(endpoints.router)
router.include_router(auth.router)
router.include_router(platform.router)
