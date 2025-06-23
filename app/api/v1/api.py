from fastapi import APIRouter
from .endpoints.auth import router as auth

api_router = APIRouter()
api_router.include_router(auth,prefix="/auth" , tags=["auth"])
