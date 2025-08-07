# app/schemas/rag.py (New file)

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

# --- Collection Schemas ---
class CollectionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class CollectionCreate(CollectionBase):
    pass

class CollectionInDB(CollectionBase):
    id: UUID
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # For Pydantic v2+

# --- Document Schemas ---
class DocumentBase(BaseModel):
    file_name: str
    status: str

class DocumentInDB(DocumentBase):
    id: UUID
    collection_id: UUID
    user_id: str
    storage_path: str
    uploaded_at: datetime

    class Config:
        from_attributes = True

# --- Document Chunk Schemas (Lightweight, primarily for Pinecone ID reference) ---
class DocumentChunkInDB(BaseModel):
    id: UUID # This is the Pinecone vector ID
    document_id: UUID
    chunk_index: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- Conversation Schemas ---
class ConversationBase(BaseModel):
    collection_id: UUID
    title: Optional[str] = None

class ConversationCreate(ConversationBase):
    pass

class ConversationInDB(ConversationBase):
    id: UUID
    user_id: str
    created_at: datetime
    last_active_at: datetime

    class Config:
        from_attributes = True

# --- Message Schemas ---
class MessageBase(BaseModel):
    sender: str # "user" or "ai"
    content: str

class MessageCreate(MessageBase):
    pass

class MessageInDB(MessageBase):
    id: UUID
    conversation_id: UUID
    timestamp: datetime
    retrieved_sources: Optional[List[str]] = None # List of document_chunks.id (Pinecone vector IDs)

    class Config:
        from_attributes = True

# --- RAG Specific Request/Response Schemas ---
class ChatMessagePayload(BaseModel):
    query: str
    collection_id: str
    conversation_id: Optional[str] = None
    # Add optional selected_pdf_id if you want to chat against a single PDF explicitly

class ChatResponseChunk(BaseModel):
    type: str # e.g., "text", "source", "end"
    content: Optional[str] = None
    source_ids: Optional[List[str]] = None # IDs of chunks used

class DocumentUploadResponse(BaseModel):
    document_id: UUID
    file_name: str
    status: str
    message: str


class ChatResponse(BaseModel):
    conversation_id: str
    ai_response: str
    retrieved_sources: Optional[List[str]] = None # IDs of chunks used    