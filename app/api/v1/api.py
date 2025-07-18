from fastapi import APIRouter
from .endpoints.auth import router as auth
from .endpoints.users import router as users
from .endpoints.tools import router as tools

api_router = APIRouter()
api_router.include_router(auth,prefix="/auth" , tags=["auth"])
api_router.include_router(users,prefix="/users", tags=["users"])   
api_router.include_router(tools,prefix="/tools", tags=["tools"]) 
