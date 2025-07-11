from fastapi import APIRouter
from app.api.v1.endpoints import generation

# Create API router for v1
router = APIRouter()

# Include endpoint routers
router.include_router(generation.router)
