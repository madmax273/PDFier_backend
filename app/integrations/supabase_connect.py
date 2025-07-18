# app/supabase_config.py
import os
from supabase import create_client, Client
from app.core.config import settings

SUPABASE_URL=settings.SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY=settings.SUPABASE_SERVICE_ROLE_KEY
SUPABASE_PDF_BUCKET_NAME=settings.SUPABASE_PDF_BUCKET_NAME

supabase_client: Client = None # Global client instance

async def initialize_supabase():
    global supabase_client
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError("Supabase URL or Service Role Key not found in environment variables.")

    if supabase_client is None:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        print("✅ Supabase client initialized successfully.")
    else:
        print("❌ Supabase client already initialized.")

async def get_supabase_client() -> Client:
    """Returns the initialized Supabase client."""
    if supabase_client is None:
        raise RuntimeError("Supabase client not initialized. Call initialize_supabase() first.")
    return supabase_client

def get_pdf_bucket_name() -> str:
    """Returns the configured Supabase PDF bucket name."""
    if not SUPABASE_PDF_BUCKET_NAME:
        raise ValueError("Supabase PDF bucket name not found in environment variables.")
    return SUPABASE_PDF_BUCKET_NAME




