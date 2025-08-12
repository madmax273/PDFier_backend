from app.database.crud import create_conversation, get_messages_by_conversation
from fastapi.responses import JSONResponse
from uuid import UUID
from supabase import Client
from app.services.auth_services import get_current_user
from fastapi import Depends
from fastapi import status
from app.integrations.supabase_connect import get_supabase_client
from app.integrations.supabase_connect import set_supabase_rls_user_context
from fastapi import APIRouter
from fastapi import HTTPException
from app.core.config import settings
from typing import Optional
from app.database.crud import get_conversations_by_collection

router = APIRouter()

@router.post("/")
async def create(
    collection_id: str,
    title: str,
    current_user: dict = Depends(get_current_user),
    supabase_client: Client = Depends(get_supabase_client),
    _rls_context: dict = Depends(set_supabase_rls_user_context),
):
    """
    Create a new conversation for a given collection.
    """
    try:
        conversation = create_conversation(supabase_client, str(current_user["_id"]), collection_id=collection_id, title=title)
        return JSONResponse(status_code=status.HTTP_201_CREATED, content={"status":"success","status_code":status.HTTP_201_CREATED,"message":"Conversation created successfully","data":conversation})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"status":"error","status_code":status.HTTP_500_INTERNAL_SERVER_ERROR,"message":"Failed to create conversation"})

@router.get("/")
async def get_conversations(
    collection_id: str,
    current_user: dict = Depends(get_current_user),
    supabase_client: Client = Depends(get_supabase_client),
    _rls_context: dict = Depends(set_supabase_rls_user_context),
):
    """
    Get all conversations for a user.
    """
    try:
        conversations = get_conversations_by_collection(supabase_client, UUID(collection_id))
        return JSONResponse(status_code=status.HTTP_200_OK, content={"status":"success","status_code":status.HTTP_200_OK,"message":"Conversations retrieved successfully","data":conversations})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"status":"error","status_code":status.HTTP_500_INTERNAL_SERVER_ERROR,"message":"Failed to get conversations"})

