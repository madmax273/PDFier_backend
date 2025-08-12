import os
from supabase import create_client, Client
from app.core.config import settings
from app.core.deps import get_current_user
from fastapi import Depends, HTTPException
from fastapi import status
from fastapi.encoders import jsonable_encoder

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


def set_supabase_rls_user_context(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client) # Get Supabase client
):
    """
    This must be called for RLS policies to work.
    """
    try:
        user_id = current_user["_id"]
        # Convert ObjectId to str before passing to Supabase RPC
        # Note: Supabase Python client's rpc() is synchronous, don't await it
        response = supabase.rpc(
            'set_app_user_id',
            {'user_id': str(user_id)}
        ).execute()

        print(f"✅ Supabase RLS context set for user {user_id}")
        
        # Check if the response contains an error
        if hasattr(response, 'error') and response.error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to set user context for database operations."
            )
    except HTTPException:
        raise
    except Exception as e:
        # Log the error, but don't necessarily raise HTTPException if it's not critical
        print(f"Error setting Supabase app.user_id for {user_id}: {e}")
        # Optionally re-raise if RLS is critical
        # raise HTTPException(
        #     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #     detail="Failed to set user context for database operations."
        # )
