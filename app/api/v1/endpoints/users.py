from fastapi import APIRouter, Depends
from app.services.auth_services import get_current_user_or_guest
from fastapi.security import HTTPAuthorizationCredentials
from app.database.models import UserModel
from app.database.connection import get_mongo_db
from bson import ObjectId
router = APIRouter()

@router.get("/me", response_model=UserModel)
async def read_users_me(
    current_user: HTTPAuthorizationCredentials = Depends(get_current_user_or_guest),
    db = Depends(get_mongo_db)
):
    user_id=current_user.get("sub")
    user = await db["users"].find_one({"_id": ObjectId(user_id)})
    return UserModel.model_validate(user)