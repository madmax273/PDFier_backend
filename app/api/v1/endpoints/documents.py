# app/api/v1/endpoints/documents.py (New File)

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks, status, Query
from uuid import UUID
from app.schemas.rag import DocumentUploadResponse
from app.database.crud import create_document, update_document_status
from app.integrations.supabase_connect import get_supabase_client,set_supabase_rls_user_context,get_pdf_bucket_name
from app.services.rag_service import process_pdf_for_rag
from supabase import Client
import io
from datetime import datetime
from app.services.auth_services import get_current_user
import logging
router = APIRouter()

@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
def upload_document(
    file: UploadFile = File(...),
    collection_id: str = Query(..., title="Collection ID", description="The ID of the collection to upload the document to"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user),
    _rls_context: None = Depends(set_supabase_rls_user_context),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Uploads a PDF document to a specified collection and starts RAG processing.
    
    This endpoint:
    1. Validates the uploaded file
    2. Saves it to Supabase Storage
    3. Creates a document record in the database
    4. Starts a background task for RAG processing
    
    Returns immediately with a 202 Accepted response while processing continues in the background.
    """
    collection_id = UUID(collection_id)
    logger = logging.getLogger(__name__)
    
    # 1. Validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Only PDF files are allowed."
        )
    
    # 2. Check user's upload quota
    try:
        # Initialize default values if not present
        usage_metrics = current_user.get("usage_metrics", {})
        pdf_uploaded_today = usage_metrics.get("pdf_uploaded_today", 0)
        pdf_upload_limit = usage_metrics.get("pdf_upload_limit_daily", 10)  # Default limit of 10 uploads per day
        
        if pdf_uploaded_today >= pdf_upload_limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail=f"Daily PDF upload limit of {pdf_upload_limit} reached. You've uploaded {pdf_uploaded_today} files today."
            )
    except Exception as e:
        logger.error(f"Error checking user upload quota: {e}")
        # Continue processing even if quota check fails
    
    try:
        # 3. Generate a safe filename with user ID and timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        safe_filename = f"{current_user['_id']}/chat_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}"
        supabase_bucket_name = get_pdf_bucket_name()

        # 4. Read file content (only once for efficiency)
        file_content_bytes = file.file.read()
        
        # 5. Upload to Supabase Storage
        try:
            res = supabase.storage.from_(supabase_bucket_name).upload(
                path=safe_filename,
                file_options={"content-type": "application/pdf"},
                file=file_content_bytes
            )
            if hasattr(res, 'error') and res.error:
                raise Exception(f"Storage error: {res.error}")
                
        except Exception as e:
            logger.error(f"Failed to upload file to storage: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Failed to upload file to storage."
            )

        # 6. Create document record in database
        try:
            new_document = create_document(
                supabase,
                collection_id,
                str(current_user['_id']),
                file.filename,
                safe_filename
            )
            document_id = new_document['id']
        except Exception as e:
            logger.error(f"Failed to create document record: {e}")
            # Clean up the uploaded file if document creation fails
            try:
                supabase.storage.from_(supabase_bucket_name).remove([safe_filename])
            except Exception as cleanup_error:
                logger.error(f"Failed to clean up storage after document creation failed: {cleanup_error}")
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create document record."
            )

        # 7. Start background task for RAG processing
        try:
            background_tasks.add_task(
                process_pdf_for_rag,
                user_id=str(current_user['_id']),
                collection_id=collection_id,
                document_id=UUID(document_id),
                file_name=file.filename,
                file_content_bytes=file_content_bytes,
                file=file,
                supabase_client=supabase  # Pass the client to avoid creating a new one
            )
        except Exception as e:
            logger.error(f"Failed to start background task: {e}")
            # Update document status to failed
            update_document_status(supabase, document_id, "failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start document processing."
            )

        # 8. Return success response
        return DocumentUploadResponse(
            document_id=UUID(document_id),
            file_name=file.filename,
            status="processing",
            message="PDF upload initiated. Processing in the background."
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error during document upload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="An unexpected error occurred during document upload."
        )

# (Optional: Add GET /documents to list documents in a collection)
# @router.get("/collection/{collection_id}/documents", response_model=List[DocumentInDB])
# async def get_documents_in_collection(
#     collection_id: UUID,
#     user_id: str = Depends(get_current_active_user),
#     _rls_context: None = Depends(apply_rls_context),
#     supabase: Client = Depends(get_supabase_client)
# ):
#     # Implement fetching documents from Supabase `documents` table
#     # RLS will ensure only documents in owned collections are returned
#     pass