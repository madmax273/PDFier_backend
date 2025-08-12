# app/services/rag_service.py

from typing import List, Dict, Any, Optional
import uuid
from uuid import UUID
from app.services.pdf_processing import extract_text_from_pdf, chunk_text
from app.services.embedding_services import generate_embedding, get_llm_completion_stream
from app.services.pinecone_services import upsert_vectors_to_pinecone, query_pinecone
from app.database.crud import create_document_chunks, get_messages_by_conversation
from app.core.config import settings
from fastapi import UploadFile
from app.integrations.supabase_connect import get_supabase_client,Client

async def process_pdf_for_rag(
    user_id: str,
    collection_id: UUID,
    document_id: UUID,
    file_name: str,
    file_content_bytes: bytes,  # Pass bytes for background task
    file:UploadFile,
    supabase_client: Client  # Pass Supabase client for DB operations
):
    """
    Orchestrates the PDF processing, embedding generation, and Pinecone upsert.
    Intended to be run as a FastAPI BackgroundTask.
    
    Args:
        user_id: ID of the user who owns the document
        collection_id: ID of the collection this document belongs to
        document_id: ID of the document being processed
        file_name: Original name of the uploaded file
        file_content_bytes: Binary content of the PDF file
        file:UploadFile,
        supabase_client: Supabase client instance for database operations
    """
    from fastapi import HTTPException
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starting RAG processing for document {document_id} in collection {collection_id}")
        
        # 1. Update document status to 'processing'
        try:
            from app.database.crud import update_document_status
            update_document_status(supabase_client, document_id, "processing")
        except Exception as e:
            logger.error(f"Failed to update document status to 'processing': {e}")
            # Continue processing even if status update fails
        logger.info(f"Document status updated to 'processing'")    

        # 2. Extract Text
        pdf_file_mock = file
        try:
            full_text = await extract_text_from_pdf(pdf_file_mock)
            if not full_text.strip():
                raise ValueError("Extracted text is empty")
        except Exception as e:
            error_msg = f"Failed to extract text from PDF: {str(e)}"
            logger.error(error_msg)
            update_document_status(supabase_client, document_id, "failed")
            raise HTTPException(status_code=400, detail=error_msg)
        logger.info(f"Text extracted from PDF")

        # 3. Chunk Text
        try:
            chunks = chunk_text(full_text, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
            if not chunks:
                raise ValueError("No text chunks generated from the document")
        except Exception as e:
            error_msg = f"Failed to chunk text: {str(e)}"
            logger.error(error_msg)
            update_document_status(supabase_client, document_id, "failed")
            raise HTTPException(status_code=400, detail=error_msg)
        logger.info(f"Text chunked")

        pinecone_vectors_data = []
        supabase_chunks_data = []
        
        # 4. Process each chunk
        for i, chunk_text_content in enumerate(chunks):
            try:
                # Generate a unique ID for the chunk
                chunk_vector_id = f"{document_id}-{i}"
                
                # Generate embedding for the chunk
                embedding = await generate_embedding(chunk_text_content)
                
                # Prepare data for Pinecone
                pinecone_vectors_data.append({
                    "id": chunk_vector_id,
                    "values": embedding,
                    "metadata": {
                    "document_id": str(document_id),
                    "collection_id": str(collection_id),
                    "file_name": file_name,
                    "chunk_index": i,
                    "content": chunk_text_content[:500]  # Store first 500 chars in metadata
                }
                })
            except Exception as e:
                logger.error(f"Error processing chunk {i}: {str(e)}")
                # Continue with next chunk even if one fails
                continue

            try:
                chunk_id = str(uuid.uuid4())
                # Ensure document_id is a valid UUID string
                supabase_chunks_data.append({
                    "id": chunk_id,
                    "document_id": str(document_id),  # Let Supabase handle UUID conversion
                    "chunk_index": i
                })
            except Exception as e:
                logger.error(f"Error processing chunk {i}: {str(e)}")
                # Continue with next chunk even if one fails
                continue                
            
        
        if not pinecone_vectors_data:
            error_msg = "No valid chunks were processed successfully"
            logger.error(error_msg)
            update_document_status(supabase_client, document_id, "failed")
            raise HTTPException(status_code=400, detail=error_msg)
        logger.info(f"Vectors generated")

        # 5. Upsert vectors to Pinecone
        try:
            logger.info(f"Upserting {len(pinecone_vectors_data)} vectors to Pinecone")
            await upsert_vectors_to_pinecone(user_id, pinecone_vectors_data)
        except Exception as e:
            error_msg = f"Failed to upsert vectors to Pinecone: {str(e)}"
            logger.error(error_msg)
            update_document_status(supabase_client, document_id, "failed")
            raise HTTPException(status_code=500, detail=error_msg)
        logger.info(f"Vectors upserted")

        # 6. Store chunk metadata in Supabase
        try:
            logger.info(f"Storing {len(supabase_chunks_data)} chunks in Supabase")
            create_document_chunks(supabase_client, supabase_chunks_data)
        except Exception as e:
            error_msg = f"Failed to store chunks in Supabase: {str(e)}"
            logger.error(error_msg)
            # Don't fail the entire process if Supabase storage fails
            # as Pinecone upsert was successful
        logger.info(f"Chunks stored")
        # 7. Update document status to completed
        try:
            update_document_status(supabase_client, document_id, "completed")
            logger.info(f"Successfully processed RAG for document {document_id} ({file_name})")
        except Exception as e:
            logger.error(f"Document processing completed but status update failed: {str(e)}")

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        error_msg = f"Unexpected error in RAG processing: {str(e)}"
        logger.error(error_msg, exc_info=True)
        try:
            update_document_status(supabase_client, document_id, "failed")
        except Exception as update_err:
            logger.error(f"Failed to update document status to 'failed': {update_err}")
        raise HTTPException(status_code=500, detail=error_msg)
    logger.info(f"Document processing completed successfully")


async def generate_rag_response_stream(
    user_id: str,
    query: str,
    collection_id: UUID,
    conversation_id: UUID,
    supabase_client: Client
):
    """
    Performs RAG query, constructs prompt, and streams LLM response and metadata.
    Yields structured content chunks and metadata.
    """
    # 1. Generate Query Embedding
    query_embedding = await generate_embedding(query)

    # 2. Retrieve relevant chunks from Pinecone
    retrieved_matches = await query_pinecone(user_id, query_embedding, collection_id, settings.TOP_K_RETRIEVAL)
    retrieved_contexts = [match.metadata['content'] for match in retrieved_matches if 'content' in match.metadata]
    retrieved_source_ids = [match.id for match in retrieved_matches]

    if not retrieved_contexts:
        yield {
            "type": "error",
            "message": "I don't have enough information in the selected documents to answer that."
        }
        return

    # 3. Retrieve recent conversation history
    conversation_history = get_messages_by_conversation(
        supabase_client, conversation_id, limit=settings.CONVERSATION_HISTORY_LIMIT
    )
    history_string = ""
    for msg in conversation_history:
        history_string += f"{msg['sender'].capitalize()}: {msg['content']}\n"
    print("constructing LLM prompt")
    # 4. Construct LLM Prompt
    context_str = "\n\n".join(retrieved_contexts)
    prompt = f"""
    You are an AI assistant specialized in answering questions based on provided documents.
    Answer the user's query only using the context provided below.
    If the answer cannot be found in the context, state that you don't have enough information.

    --- Conversation History ---
    {history_string}

    --- Retrieved Document Context ---
    {context_str}

    --- User Query ---
    {query}

    Answer:
    """

    # 5. Stream LLM Response
    print("Streaming LLM response")
    async for chunk in get_llm_completion_stream(prompt):
        yield {
            "type": "response",
            "data": chunk
        }

    # 6. Final metadata
    yield {
        "type": "metadata",
        "sources": retrieved_source_ids,
        "contexts": retrieved_contexts,
    }
