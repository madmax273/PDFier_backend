from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from app.database.crud import get_messages_by_conversation
from app.integrations.supabase_connect import get_supabase_client, Client
from app.core.config import settings
from fastapi.responses import JSONResponse
from app.services.auth_services import get_current_user
from fastapi import status
from app.integrations.supabase_connect import set_supabase_rls_user_context
from app.schemas.rag import MessageOutDB
from typing import List
from fastapi.encoders import jsonable_encoder
router = APIRouter()

@router.get("/")
async def get_message_by_conversation(
    conversation_id: str,
    current_user: str = Depends(get_current_user),
    supabase_client: Client = Depends(get_supabase_client),
    _rls_context: dict = Depends(set_supabase_rls_user_context),
):
    """
    Get all messages for a given conversation.
    """
    try:
        messages = get_messages_by_conversation(supabase_client, UUID(conversation_id),limit=settings.CONVERSATION_HISTORY_LIMIT)
        print("messages",messages)
        # messages = [MessageOutDB(**message) for message in messages]
        message=[MessageOutDB(**message) for message in messages]
        messages=jsonable_encoder(message)
        
        return JSONResponse(status_code=status.HTTP_200_OK, content={"status":"success","status_code":status.HTTP_200_OK,"message":"Messages retrieved successfully","data":messages})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"status":"error","status_code":status.HTTP_500_INTERNAL_SERVER_ERROR,"message":"Failed to get messages"})
