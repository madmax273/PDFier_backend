from app.services.auth_services import get_current_user
from fastapi import status,HTTPException,Depends



# async def get_current_user_id(current_user: dict = Depends(get_current_user)) -> str:
#     """
#     Dependency to extract and validate user_id from JWT in Authorization header.
#     """
#     if not current_user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid token",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     return current_user["_id"]


