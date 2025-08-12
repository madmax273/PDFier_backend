from fastapi import APIRouter
from .endpoints.auth import router as auth
from .endpoints.users import router as users
from .endpoints.tools import router as tools
from .endpoints.chat_ai import router as chat
from .endpoints.collections import router as collections
from .endpoints.documents import router as documents
from .endpoints.conversations import router as conversations
from .endpoints.messages import router as messages

api_router = APIRouter()
api_router.include_router(auth,prefix="/auth" , tags=["auth"])
api_router.include_router(users,prefix="/users", tags=["users"])   
api_router.include_router(tools,prefix="/tools", tags=["tools"]) 
api_router.include_router(chat,prefix="/chat", tags=["chat"]) 
api_router.include_router(collections,prefix="/collections", tags=["collections"])
api_router.include_router(documents,prefix="/documents", tags=["documents"])
api_router.include_router(conversations,prefix="/conversations", tags=["conversations"])
api_router.include_router(messages,prefix="/messages", tags=["messages"])


