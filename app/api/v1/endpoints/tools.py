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

router = APIRouter()

@router.post("/pdf/merge")
async def merge_pdf(
    files: List[UploadFile] = File(...),
    current_user: dict | None = Depends(get_current_user_or_guest),
    db=Depends(get_mongo_db)
):
   
    if not current_user:
        print("Guest user")

        return JSONResponse(content={"status":"error","status_code":401, "message":"Guest"},status_code=status.HTTP_401_UNAUTHORIZED)

    if len(files) < 2:
        raise HTTPException(detail={"status":"error","status_code":400, "message":"Please upload at least two PDF files to merge."},status_code=status.HTTP_400_BAD_REQUEST)

    # Quota check (for logged-in users)
    if current_user.get("usage_metrics").get("pdf_processed_today") >= current_user.get("usage_metrics").get("pdf_processed_limit_daily"):
        raise HTTPException(detail={"status":"error","status_code":403, "message":"Daily PDF merge limit exceeded. Please upgrade your plan."},status_code=status.HTTP_403_FORBIDDEN)

    merger = PdfMerger()
    merged_pdf_stream = BytesIO()

    try:
        for upload_file in files:
            if upload_file.content_type != "application/pdf":
                raise HTTPException(detail={"status":"error","status_code":400, "message":f"File {upload_file.filename} is not a PDF."},status_code=status.HTTP_400_BAD_REQUEST)
            
            file_content = await upload_file.read()
            merger.append(BytesIO(file_content))
        
        merger.write(merged_pdf_stream)
        merger.close()
        merged_pdf_stream.seek(0)
        
        print("merged_pdf_stream")
        # Upload Merged PDF to Firebase Storage
        supabase_client = await get_supabase_client()
        bucket=get_pdf_bucket_name()
        # Define the path in Firebase Storage. Use user ID for organization.
        merged_filename = f"{current_user['_id']}/merged_pdf_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
        file_path = f"{bucket}/{merged_filename}"
        bucket_client = supabase_client.storage.from_(bucket).upload(file_path, merged_pdf_stream.getvalue())
        
        # Generate a signed URL for download (valid for 30 minutes)
        # This URL will be returned to the frontend for direct download.
        download_url = supabase_client.storage.from_(bucket).create_signed_url(file_path, 1800)
        # Update User Usage in MongoDB

        current_pdf_processed_today=current_user['usage_metrics']['pdf_processed_today']
        # Update the user's usage count
        updated_user_doc = await db["users"].find_one_and_update(
            {"_id": ObjectId(current_user['_id'])},
            {"$inc": {"usage_metrics.pdf_processed_today": 1}},
            return_document=True  # This ensures we get the updated document
        )

        # Convert ObjectId to string for JSON serialization
        updated_user_doc['_id'] = str(updated_user_doc['_id'])
        updated_user_doc = jsonable_encoder(updated_user_doc)

        return JSONResponse(content={
            "status":"success",
            "message": "PDFs merged and uploaded successfully!",
            "download_url": download_url,
            "user_usage": updated_user_doc.get('usage_metrics', {})
        }, status_code=status.HTTP_200_OK)

    except Exception as e:
        print(f"Error during PDF merge or upload: {e}")
        raise HTTPException(detail={"status":"error","status_code":500, "message":f"Failed to merge or upload PDFs: {e}"},status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)