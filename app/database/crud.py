# app/database/crud.py (New functions)

from typing import List, Dict, Any, Optional
from uuid import UUID
from supabase import Client
from app.schemas.rag import CollectionCreate, DocumentInDB, DocumentChunkInDB, ConversationInDB, MessageInDB # Import your schemas
from datetime import datetime

# --- Collections CRUD ---
def create_collection(
    supabase: Client, user_id: str, collection_data: CollectionCreate
) -> Dict[str, Any]:
    response = supabase.table('collections').insert({
        "user_id": user_id,
        "name": collection_data.name,
        "description": collection_data.description
    }).execute()
    
    if hasattr(response, 'error') and response.error:
        raise Exception(f"Supabase error: {response.error}")
        
    return response.data[0] if response.data else None

def get_collections_by_user(supabase: Client, user_id: str) -> List[Dict[str, Any]]:
    """
    Get all collections for a user.
    RLS will automatically filter by user_id due to the set_supabase_rls_user_context dependency.
    """
    response = supabase.table('collections').select('*').execute()
    
    if hasattr(response, 'error') and response.error:
        raise Exception(f"Supabase error: {response.error}")
        
    return response.data if response.data else []

# --- Documents CRUD ---
def create_document(
    supabase: Client, collection_id: UUID, user_id: str, file_name: str, storage_path: str
) -> Dict[str, Any]:
    response = supabase.table('documents').insert({
        "collection_id": str(collection_id),
        "user_id": user_id,
        "file_name": file_name,
        "storage_path": storage_path,
        "status": "processing"
    }).execute()
    
    # Check for errors in the response
    if hasattr(response, 'error') and response.error:
        raise Exception(f"Supabase error: {response.error}")
        
    if not response.data or len(response.data) == 0:
        raise Exception("No data returned from document creation")
        
    return response.data[0]

def update_document_status(
    supabase: Client, document_id: UUID, status: str
) -> Dict[str, Any]:
    response = supabase.from_('documents').update({"status": status}).eq('id', str(document_id)).execute()
    
    if hasattr(response, 'error') and response.error:
        raise Exception(f"Supabase error updating document status: {response.error}")
        
    if not response.data or len(response.data) == 0:
        raise Exception("No data returned from document status update")
        
    return response.data[0]

def get_documents_by_collection(
    supabase: Client, collection_id: UUID
) -> List[Dict[str, Any]]:
    response = supabase.table('documents').select('*').eq('collection_id', str(collection_id)).execute()
    
    if hasattr(response, 'error') and response.error:
        raise Exception(f"Supabase error getting documents: {response.error}")
        
    return response.data if response.data else []    

# --- Document Chunks CRUD ---
def create_document_chunks(
    supabase: Client, chunks_data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Insert document chunks into the database.
    
    Args:
        supabase: Supabase client
        chunks_data: List of chunk dictionaries with 'id', 'document_id', and 'chunk_index'
        
    Returns:
        List of inserted chunks
    """
    if not chunks_data:
        return []
        
    try:
        # Convert to list of dicts with only the required fields
        insert_data = [
            {
                'id': str(chunk.get('id')),
                'document_id': str(chunk.get('document_id')),  # Let Supabase handle UUID conversion
                'chunk_index': int(chunk.get('chunk_index', 0))
            }
            for chunk in chunks_data
        ]
        
        # Insert in batches to avoid hitting URL length limits
        batch_size = 100
        results = []
        
        for i in range(0, len(insert_data), batch_size):
            batch = insert_data[i:i + batch_size]
            response = supabase.table('document_chunks').insert(batch).execute()
            
            if hasattr(response, 'error') and response.error:
                raise Exception(f"Supabase error creating document chunks: {response.error}")
                
            if response.data:
                results.extend(response.data)
        
        return results
        
    except Exception as e:
        error_msg = f"Error in create_document_chunks: {str(e)}"
        print(error_msg)  # Log the error for debugging
        raise Exception(error_msg)

# --- Conversations CRUD ---
def create_conversation(
    supabase: Client, user_id: str, collection_id: str, title: Optional[str] = None
) -> Dict[str, Any]:
    response = supabase.from_('conversations').insert({
        "user_id": user_id,
        "collection_id": collection_id,
        "title": title or f"Chat in {collection_id}" # Default title
    }).execute()
    
    print(f"Creating conversation {collection_id} for user {user_id}")
    
    if hasattr(response, 'error') and response.error:
        print(f"Supabase error creating conversation: {response.error}")
        raise HTTPException(status_code=500, detail=f"Supabase error creating conversation: {response.error}")
        
    if not response.data or len(response.data) == 0:
        print("No data returned from conversation creation")
        raise HTTPException(status_code=500, detail="No data returned from conversation creation")
        
    print(f"Conversation {collection_id} created for user {user_id}")
    return response.data[0]

def get_conversation_by_id(
    supabase: Client, conversation_id: UUID
) -> Optional[Dict[str, Any]]:
    response = supabase.from_('conversations').select('*').eq('id', str(conversation_id)).limit(1).execute()
    
    if hasattr(response, 'error') and response.error:
        raise Exception(f"Supabase error getting conversation: {response.error}")
        
    return response.data[0] if response.data and len(response.data) > 0 else None

def get_conversations_by_collection(
    supabase: Client, collection_id: UUID
) -> List[Dict[str, Any]]:
    # RLS will ensure only user's conversations in their collections are returned
    response = supabase.from_('conversations').select('*').eq('collection_id', str(collection_id)).order('last_active_at', desc=True).execute()
    
    if hasattr(response, 'error') and response.error:
        raise Exception(f"Supabase error getting conversations: {response.error}")
        
    return response.data if response.data else []

# --- Messages CRUD ---
def create_message(
    supabase: Client, conversation_id: UUID, sender: str, content: str, retrieved_sources: Optional[List[str]] = None
) -> Dict[str, Any]:
    message_data = {
        "conversation_id": str(conversation_id),
        "sender": sender,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    }
    if retrieved_sources:
        message_data["retrieved_sources"] = retrieved_sources # Stores as JSONB

    response = supabase.from_('messages').insert(message_data).execute()
    
    if hasattr(response, 'error') and response.error:
        raise Exception(f"Supabase error creating message: {response.error}")
        
    if not response.data or len(response.data) == 0:
        raise Exception("No data returned from message creation")
        
    return response.data[0]

def get_messages_by_conversation(
    supabase: Client, conversation_id: UUID, limit: int = 10
) -> List[Dict[str, Any]]:
    print(f"get_messages_by_conversation: {conversation_id} {limit}")
    # RLS will ensure messages from owned conversations are returned
    response = supabase.from_('messages').select('*').eq('conversation_id', str(conversation_id)).order('timestamp', desc=True).limit(limit).execute()
    
    if hasattr(response, 'error') and response.error:
        print(f"Supabase error getting messages: {response.error}")
        raise Exception(f"Supabase error getting messages: {response.error}")
        
    print(f"get_messages_by_conversation: {response.data}")
    return response.data if response.data else []