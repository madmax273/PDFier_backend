from fastapi import File, UploadFile,Depends,APIRouter,Request,HTTPException,status
from PyPDF2 import PdfMerger # Ensure this is imported
from app.database.connection import get_mongo_db
from app.services.auth_services import get_current_user_or_guest
from app.integrations.supabase_connect import get_supabase_client,get_pdf_bucket_name
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from datetime import datetime, timedelta
from io import BytesIO
from typing import List
from bson.objectid import ObjectId
from fastapi.encoders import jsonable_encoder
from fastapi import Form
import fitz  # PyMuPDF
from app.core.config import settings
import os
from app.utils.compress import compress_pdf_content

router = APIRouter()


# Assume router and all dependencies (get_current_user_or_guest, etc.) are defined

@router.post("/pdf/merge")
async def merge_pdf(
    files: List[UploadFile] = File(...),
    current_user: dict | None = Depends(get_current_user_or_guest),
    db=Depends(get_mongo_db)
):
    if len(files) < 2:
        raise HTTPException(detail={"status":"error", "message":"Please upload at least two PDF files."}, status_code=status.HTTP_400_BAD_REQUEST)

    if current_user and current_user["usage_metrics"]["pdf_processed_today"] >= current_user["usage_metrics"]["pdf_processed_limit_daily"]:
        raise HTTPException(detail={"status":"error", "message":"Daily PDF merge limit exceeded."}, status_code=status.HTTP_403_FORBIDDEN)

    merger = PdfMerger()
    merged_pdf_stream = BytesIO()

    try:
        # --- 1. Filename Logic (Corrected) ---
        # Use the name of the *first* uploaded file as the base for the new filename.
        original_name = files[0].filename
        if original_name:
            base_name = os.path.splitext(original_name)[0]
        else:
            # Provide a default name if the first file has no name
            base_name = "merged_file"

        # --- 2. PDF Merging ---
        for upload_file in files:
            if upload_file.content_type != "application/pdf":
                raise HTTPException(detail={"status":"error", "message":f"File {upload_file.filename} is not a PDF."}, status_code=status.HTTP_400_BAD_REQUEST)
            
            file_content = await upload_file.read()
            merger.append(BytesIO(file_content))
        
        merger.write(merged_pdf_stream)
        merger.close()
        merged_pdf_stream.seek(0)
        
        # --- 3. Supabase Upload (Corrected) ---
        supabase_client = await get_supabase_client()
        bucket = get_pdf_bucket_name()
        
        # Define the final path INSIDE the bucket
        if current_user:
            file_path = f"{current_user['_id']}/{base_name}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
        else:
            file_path = f"guest/{base_name}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"

        print(f"Uploading to Supabase with path: {file_path}") # For debugging

        # Upload the file, passing the stream object directly
        supabase_client.storage.from_(bucket).upload(
            path=file_path, 
            file=merged_pdf_stream.getvalue(), # Reverted to .getvalue()
            file_options={"contentType": "application/pdf"}
        )
        
        # --- 4. Generate Signed URL ---
        url_response = supabase_client.storage.from_(bucket).create_signed_url(file_path, 1800)
        download_url = url_response['signedURL']

        # --- 5. Update Database ---
        updated_user_doc = None
        if current_user:
            updated_user_doc = await db["users"].find_one_and_update(
                {"_id": ObjectId(current_user['_id'])},
                {"$inc": {"usage_metrics.pdf_processed_today": 1}},
                return_document=True
            )
            updated_user_doc['_id'] = str(updated_user_doc['_id'])
            updated_user_doc = jsonable_encoder(updated_user_doc)

        return JSONResponse(content={
            "status": "success",
            "message": "PDFs merged and uploaded successfully!",
            "download_url": download_url,
            "user_usage": updated_user_doc.get('usage_metrics', {}) if current_user else None
        }, status_code=status.HTTP_200_OK)

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error during PDF merge or upload: {e}")
        raise HTTPException(detail={"status":"error", "message":"An internal error occurred."}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/pdf/compress")
async def compress_pdf(
    files: List[UploadFile] = File(...),
    compression_level: str = Form("medium", description="Compression level (low, medium, high)"),
    current_user: dict | None = Depends(get_current_user_or_guest),
    db=Depends(get_mongo_db)
):
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"status": "error", "message": "No files provided"}
        )

    # Quota check (for logged-in users)
    if current_user and current_user["usage_metrics"]["pdf_processed_today"] >= current_user["usage_metrics"]["pdf_processed_limit_daily"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"status": "error", "message": "Daily PDF processing limit exceeded."}
        )

    try:
        supabase_client = await get_supabase_client()
        bucket = get_pdf_bucket_name()
        compressed_urls = []

        for upload_file in files:
            if upload_file.content_type != "application/pdf":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"status": "error", "message": f"File {upload_file.filename} is not a PDF."}
                )

            # Read the PDF file
            file_content = await upload_file.read()
            
            # Compress the PDF
            compressed_content = compress_pdf_content(file_content, compression_level)
            
            # Generate filename and path
            original_name = upload_file.filename or "compressed_file"
            base_name = os.path.splitext(original_name)[0]
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            
            if current_user:
                file_path = f"{current_user['_id']}/{base_name}_compressed_{timestamp}.pdf"
            else:
                file_path = f"guest/{base_name}_compressed_{timestamp}.pdf"

            # Upload to Supabase
            supabase_client.storage.from_(bucket).upload(
                path=file_path,
                file=compressed_content,
                file_options={"contentType": "application/pdf"}
            )
            SUPABASE_URL=settings.SUPABASE_URL
            # Generate signed URL
            url_response = supabase_client.storage.from_(bucket).create_signed_url(file_path, 1800)
            compressed_urls.append(url_response['signedURL'])

        # Update user usage if logged in
        updated_user_doc = None
        if current_user:
            updated_user_doc = await db["users"].find_one_and_update(
                {"_id": ObjectId(current_user['_id'])},
                {"$inc": {"usage_metrics.pdf_processed_today": 1}},
                return_document=True
            )
            updated_user_doc['_id'] = str(updated_user_doc['_id'])
            updated_user_doc = jsonable_encoder(updated_user_doc)

        return JSONResponse(
            content={
                "status": "success",
                "message": "PDFs compressed and uploaded successfully!",
                "download_urls": compressed_urls,
                "user_usage": updated_user_doc.get('usage_metrics', {}) if updated_user_doc else None
            },
            status_code=status.HTTP_200_OK
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error during PDF compression: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "message": f"Failed to compress PDFs: {str(e)}"}
        )


