from app.database.connection import get_mongo_db
from app.core.security import decode_token
from app.database.models import UserModel
from fastapi import Depends, HTTPException, status
from bson import ObjectId
from datetime import datetime
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.plans import get_initial_usage_metrics # Assuming this is the helper for current limits
from datetime import datetime, date
from typing import Union

security_scheme = HTTPBearer() # Define a security scheme for protected routes

async def get_current_user_or_guest(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db = Depends(get_mongo_db)
) -> Union[UserModel, None]:
    """
    Dependency that returns the current user if authenticated, or None for guests.
    """
    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if not user_id:
            return None
            
        user_doc = await db["users"].find_one({"_id": ObjectId(user_id)})
        if not user_doc:
            return None
            
        # Handle quota resets for authenticated users
        await _handle_quota_reset(user_doc, db)
        return UserModel.model_validate(user_doc)
        
    except (JWTError, HTTPException):
        return None

async def _handle_quota_reset(user_doc: dict, db):
    """Handle quota reset logic for authenticated users"""
    current_date_utc = datetime.utcnow().date()
    last_reset_date_str = user_doc.get("usage_metrics", {}).get("last_quota_reset_date")
    
    last_reset_date = None
    if last_reset_date_str:
        try:
            last_reset_date = datetime.fromisoformat(last_reset_date_str).date()
        except ValueError:
            pass

    if not last_reset_date or last_reset_date < current_date_utc:
        user_doc["usage_metrics"]["last_quota_reset_date"] = datetime.utcnow().isoformat()
        user_doc["usage_metrics"]["pdf_processed_today"] = 0
        user_doc["usage_metrics"]["word_conversions_today"] = 0
        
        current_month = datetime.utcnow().strftime("%Y-%m")
        last_reset_month = datetime.fromisoformat(last_reset_date_str).strftime("%Y-%m") if last_reset_date_str else None
        if not last_reset_month or last_reset_month < current_month:
            user_doc["usage_metrics"]["rag_queries_this_month"] = 0
            user_doc["usage_metrics"]["rag_indexed_documents_count"] = 0

        await db["users"].update_one(
            {"_id": ObjectId(user_doc["_id"])},
            {"$set": {"usage_metrics": user_doc["usage_metrics"]}}
        )
