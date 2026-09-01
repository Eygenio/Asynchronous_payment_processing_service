from fastapi import APIRouter, Depends

from src.presentation.api.v1.router import v1_router
from src.presentation.dependencies import verify_api_key

api_router = APIRouter(prefix="/api", dependencies=[Depends(verify_api_key)])
api_router.include_router(v1_router)
