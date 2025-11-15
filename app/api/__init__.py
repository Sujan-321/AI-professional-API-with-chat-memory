from fastapi import APIRouter
from .conversate import router as conversate_router

router = APIRouter()
router.include_router(conversate_router, prefix="/v1")
