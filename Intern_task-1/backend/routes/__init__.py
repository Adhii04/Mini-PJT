"""
Backend Routes Package Initialization
=====================================
Registers all modular route controllers into the central API router.
"""

from fastapi import APIRouter
from backend.routes.dataset import router as dataset_router
from backend.routes.training import router as training_router
from backend.routes.analytics import router as analytics_router
from backend.routes.agents import router as agents_router
from backend.routes.ablation import router as ablation_router

api_router = APIRouter()
api_router.include_router(dataset_router)
api_router.include_router(training_router)
api_router.include_router(analytics_router)
api_router.include_router(agents_router)
api_router.include_router(ablation_router)

__all__ = ['api_router']
