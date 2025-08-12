# app/services/pinecone_service.py


from typing import List, Dict, Any
from uuid import UUID
from app.integrations.vector_db import get_pinecone_index
from app.core.config import settings
import asyncio

async def upsert_vectors_to_pinecone(
    user_id: str, vectors_data: List[Dict[str, Any]]
):
    """Upserts vectors to the user's specific Pinecone namespace."""
    pinecone_index = await get_pinecone_index()
    namespace = f"user-{user_id}"
    try:
        # Each dict in vectors_data should have 'id', 'values', 'metadata'
        # The Pinecone client's upsert method handles batch operations efficiently
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: pinecone_index.upsert(vectors=vectors_data, namespace=namespace, batch_size=100)
        )
        print(f"Successfully upserted {len(vectors_data)} vectors to Pinecone for user {user_id} in namespace {namespace}.")
        return response
    except Exception as e:
        print(f"Error upserting vectors to Pinecone for user {user_id}: {e}")
        raise RuntimeError(f"Failed to upsert vectors to Pinecone: {e}")

async def query_pinecone(
    user_id: str,
    query_embedding: List[float],
    collection_id: UUID,
    top_k: int = settings.TOP_K_RETRIEVAL
) -> List[Dict[str, Any]]:
    """Queries Pinecone for relevant document chunks."""
    pinecone_index = await get_pinecone_index()
    namespace = f"user-{user_id}"

    # Define filter to search only within the specified collection
    pinecone_filter = {
        "collection_id": str(collection_id) # Pinecone metadata values are strings
    }

    try:
        response = pinecone_index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True, # Essential to get back chunk content
            namespace=namespace,
            filter=pinecone_filter
        )
        return response.matches
    except Exception as e:
        print(f"Error querying Pinecone for user {user_id}: {e}")
        raise RuntimeError(f"Failed to query Pinecone: {e}")