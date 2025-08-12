# app/api/v1/endpoints/collections.py (New File)

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.rag import CollectionCreate, CollectionInDB, CollectionOutDB
from app.database.crud import create_collection, get_collections_by_user
from app.integrations.supabase_connect import get_supabase_client,set_supabase_rls_user_context
from supabase import Client
from typing import List
from app.services.auth_services import get_current_user
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_new_collection(
    collection_data: CollectionCreate,
    current_user: dict = Depends(get_current_user),
    # This ensures RLS context is set for the Supabase call below
    _rls_context: None = Depends(set_supabase_rls_user_context),
    supabase: Client = Depends(get_supabase_client)
):
    """Create a new document collection for the current user."""
    user_id = str(current_user["_id"])
    try:
        new_collection = create_collection(supabase, user_id, collection_data)
        if not new_collection:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create collection: No data returned"
            )
        return JSONResponse(
            content={
                "status": "success",
                "message": "Collection created successfully!",
                "data": jsonable_encoder(new_collection),

            },
            status_code=status.HTTP_201_CREATED
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create collection: {str(e)}"
        )

@router.get("/")
def get_all_user_collections(
    current_user: dict = Depends(get_current_user),
    _rls_context: None = Depends(set_supabase_rls_user_context),
    supabase: Client = Depends(get_supabase_client)
):
    """Retrieve all document collections for the current user."""
    user_id = str(current_user["_id"])
    try:
        collections = get_collections_by_user(supabase, user_id)
        if not collections:
            return JSONResponse(
                content={
                    "status": "success",
                    "message": "Collections retrieved successfully!",
                    "data": [],
                },
                status_code=status.HTTP_200_OK
            )
        
        return JSONResponse(
            content={
                "status": "success",
                "message": "Collections retrieved successfully!",
                "data": jsonable_encoder(CollectionOutDB.model_validate(collection) for collection in collections),
            },
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve collections: {str(e)}"
        )