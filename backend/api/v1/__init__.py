"""API v1 module"""
from fastapi import APIRouter

from api.v1 import endpoints, auth, platform, github_skills
from api import skill_market

# Combine all routers
router = APIRouter(prefix="/api/v1")

# Include routers
router.include_router(endpoints.router)
router.include_router(auth.router)
router.include_router(platform.router)

# Include skill market router
# The skill_market router has prefix="/api/skills", we need to change it to work under /api/v1
skill_market.router.prefix = "/skills"  # Will become /api/v1/skills
router.include_router(skill_market.router)

# Include github skills router
# github_skills router has prefix="/github-skills", will become /api/v1/github-skills
router.include_router(github_skills.router)
