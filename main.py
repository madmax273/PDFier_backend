from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os
from pydantic import BaseModel
import uvicorn
from datetime import datetime
from app.core.lifespan import lifespan
from app.api.v1.api import api_router
from app.core.config import settings

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
    allow_origins=["https://localhost:3000"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Create uploads directory if it doesn't exist


@app.get("/")
async def root():
    """Root endpoint to check if the API is running."""
    return {
        "message": "Welcome to PDFier API",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    uvicorn.run("main:app",
     host="0.0.0.0", port=8000, 
     reload=True,
     ssl_keyfile="localhost+1-key.pem",
     ssl_certfile="localhost+1.pem")
