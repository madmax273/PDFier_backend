from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os
from pydantic import BaseModel
import uvicorn
from datetime import datetime
from app.core.lifespan import lifespan

# Initialize FastAPI app
app = FastAPI(
    title="PDFier API",
    description="API for PDF processing and management",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class PDFResponse(BaseModel):
    filename: str
    content_type: str
    size: int
    saved_path: str
    message: str

@app.get("/")
async def root():
    """Root endpoint to check if the API is running."""
    return {
        "message": "Welcome to PDFier API",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/upload/", response_model=PDFResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file to the server.
    
    Args:
        file: The PDF file to upload
        
    Returns:
        PDFResponse: Information about the uploaded file
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # Save the uploaded file
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        file_size = os.path.getsize(file_path)
        
        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": file_size,
            "saved_path": file_path,
            "message": "File uploaded successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/files/")
async def list_files():
    """List all uploaded PDF files."""
    try:
        files = []
        for filename in os.listdir(UPLOAD_DIR):
            if filename.lower().endswith('.pdf'):
                file_path = os.path.join(UPLOAD_DIR, filename)
                file_size = os.path.getsize(file_path)
                files.append({
                    "filename": filename,
                    "size_bytes": file_size,
                    "uploaded_at": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                })
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
