from fastapi import APIRouter, Depends
from app.services.auth_services import get_current_user_or_guest
from fastapi.security import HTTPAuthorizationCredentials
from app.database.connection import get_mongo_db
from bson import ObjectId
from fastapi.responses import JSONResponse
from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException
from app.schemas.users import UserOut

router = APIRouter()

@router.get("/me")
async def read_users_me(
    current_user: dict|None = Depends(get_current_user_or_guest),
    db = Depends(get_mongo_db)
):
    try:
        if not current_user:
            print("Guest user")
            return JSONResponse(content={"status":"error","status_code":401, "message":"Token Not send Guest User"},status_code=status.HTTP_401_UNAUTHORIZED)

        user_id=current_user.get("_id")
        print("user_id",user_id)
        user = await db["users"].find_one({"_id": ObjectId(user_id)})
        return JSONResponse(content={
            "status":"success",
            "message":"User data",
            "data": jsonable_encoder(UserOut.model_validate(user))
            },
            status_code=status.HTTP_200_OK)
            
    except HTTPException as e:
        raise 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))    
         