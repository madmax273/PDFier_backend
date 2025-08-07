# from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, HTTPException
# from typing import Optional, List, Dict, Any
# import json
# import logging
# from uuid import UUID
# from datetime import datetime
# from fastapi import Depends
# from app.core.config import settings
# from app.database.connection import get_mongo_db
# from app.database.crud import create_conversation, create_message, get_messages_by_conversation
# from app.integrations.supabase_connect import get_supabase_client, set_supabase_rls_user_context
# from app.schemas.rag import ChatMessagePayload, ChatResponse
# from app.services.rag_service import generate_rag_response_stream
# from app.services.embedding_services import generate_embedding
# from app.services.pinecone_services import query_pinecone
# from supabase import Client
# from app.services.auth_services import get_current_user
# from fastapi.responses import HTMLResponse
# router = APIRouter()
# logger = logging.getLogger(__name__)

# @router.get("/ws-doc")
# def websocket_doc():
#     return {
#         "message": "This is a WebSocket endpoint. Please connect using a WebSocket client.",
#         "ws_url": "/ws",
#         "expected_payload": {
#             "token": "Your JWT",
#             "collection_id": "UUID string",
#             "conversation_id": "Optional UUID string"
#         }
#     }

# @router.get("/ws-test", response_class=HTMLResponse)
# def websocket_test():
#     return """
#     <html>
#     <body>
#     <h1>Test /ws WebSocket Endpoint</h1>
#     <div>
#         <label>JWT: <input id="jwt" type="text" size="60" /></label><br>
#         <label>Collection ID: <input id="collection_id" type="text" size="40" value="69d2252a-9c41-4802-aea4-68d8a7be1388" /></label><br>
#         <label>Conversation ID (optional): <input id="conversation_id" type="text" size="40" value="" /></label><br>
#         <button onclick="connectWS()">Connect</button>
#     </div>
#     <hr>
#     <textarea id="log" cols="80" rows="20" readonly></textarea><br>
#     <input id="msg" type="text" size="60" /> <button onclick="sendMsg()">Send Message</button>
#     <script>
#         let ws;
#         function log(msg) {
#             document.getElementById("log").value += "\\n" + msg;
#         }
#         window.connectWS = function() {
#             const jwt = document.getElementById("jwt").value;
#             const collectionId = document.getElementById("collection_id").value;
#             const conversationId = document.getElementById("conversation_id").value;
#             if (!jwt) {
#                 log('Please enter a JWT.');
#                 return;
#             }
#             let wsUrl = (location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws?token=' + encodeURIComponent(jwt);
#             ws = new WebSocket(wsUrl);
#             ws.onopen = () => {
#                 log('WebSocket connected! Sending handshake...');
#                 let handshake = { collection_id: collectionId };
#                 if (conversationId) handshake.conversation_id = conversationId;
#                 ws.send(JSON.stringify(handshake));
#             };
#             ws.onmessage = e => {
#                 log('RECV: ' + e.data);
#             };
#             ws.onerror = e => {
#                 log('WebSocket error: ' + e.message);
#             };
#             ws.onclose = e => {
#                 log('WebSocket closed.');
#             };
#         }
#         window.sendMsg = function() {
#             const msg = document.getElementById("msg").value;
#             if (!ws || ws.readyState !== 1) {
#                 log('WebSocket not connected.');
#                 return;
#             }
#             ws.send(JSON.stringify({ query: msg }));
#             log('SENT: ' + msg);
#         }
#     </script>
#     </body>
#     </html>
#     """


# from fastapi import Query

# @router.websocket("/ws")
# async def websocket_chat_endpoint(
#     websocket: WebSocket,
#     token: str = Query(None),
#     db=Depends(get_mongo_db),
#     supabase_client: Client = Depends(get_supabase_client),
#     collection_id: str="69d2252a-9c41-4802-aea4-68d8a7be1388",
#     conversation_id: Optional[str] =None,
#     ):
#     """
#     WebSocket endpoint for handling real-time chat with RAG capabilities.
#     """
#     await websocket.accept()
    
#     try:
#         # Initial handshake - expect authentication and collection info
#         first_message = await websocket.receive_text()
#         initial_data = json.loads(first_message)
            
#         # Authenticate user
        
#         if not token:
#             logger.error("No token provided")
#             await websocket.close(code=4401)
#             return

#         payload = decode_token(token)
#         user_id = payload.get("sub") if payload else None
#         if not user_id:
#             logger.error("Invalid token")
#             await websocket.close(code=4401)
#             return
    
        
#         # Handle conversation (create new or use existing)
#         if conversation_id:
#             conversation_id = UUID(conversation_id)
#             # TODO: Verify conversation belongs to user/collection
#         else:
#             new_conv = await create_conversation(supabase_client, user_id, collection_id)
#             conversation_id = UUID(new_conv['id'])
#             await websocket.send_text(json.dumps({
#                 "type": "conversation_id",
#                 "content": str(conversation_id)
#             }))
        
#         # Send initial status
#         await websocket.send_text(json.dumps({
#             "type": "status",
#             "content": "Connected. Ready to chat."
#         }))

#         # Main message processing loop
#         while True:
#             try:
#                 # Wait for a message from the client
#                 message_text = await websocket.receive_text()
                
#                 # Parse and validate the message
#                 try:
#                     chat_payload = ChatMessagePayload.model_validate_json(message_text)
#                 except Exception as e:
#                     logger.error(f"Invalid message format: {str(e)}")
#                     await websocket.send_text(json.dumps({
#                         "type": "error",
#                         "content": f"Invalid message format: {str(e)}"
#                     }))
#                     continue

#                 # Store the user's message
#                 await create_message(
#                     supabase_client,
#                     conversation_id,
#                     "user",
#                     chat_payload.query
#                 )

#                 # Notify client that we're processing
#                 await websocket.send_text(json.dumps({
#                     "type": "status",
#                     "content": "Searching for relevant information..."
#                 }))

#                 # Generate and stream the RAG response
#                 full_response = ""
#                 retrieved_source_ids = []

#                 try:
#                     # Get relevant context using the query
#                     query_embedding = await generate_embedding(chat_payload.query)
#                     retrieved_matches = await query_pinecone(
#                         user_id=user_id,
#                         query_embedding=query_embedding,
#                         collection_id=collection_id,
#                         top_k=settings.TOP_K_RETRIEVAL
#                     )
                    
#                     # Extract source IDs from matches
#                     retrieved_source_ids = [
#                         match.id for match in retrieved_matches 
#                         if hasattr(match, 'id') and match.id
#                     ]
                    
#                     # Generate and stream the response
#                     async for chunk in generate_rag_response_stream(
#                         user_id=user_id,
#                         query=chat_payload.query,
#                         collection_id=collection_id,
#                         conversation_id=conversation_id,
#                         supabase_client=supabase_client,
#                         context=[{"content": match.metadata.get('text', '')} for match in retrieved_matches]
#                     ):
#                         if chunk.startswith("[ERROR]"):
#                             logger.error(chunk)
#                             await websocket.send_text(json.dumps({
#                                 "type": "error",
#                                 "content": chunk
#                             }))
#                             full_response += chunk
#                             break
#                         else:
#                             await websocket.send_text(json.dumps({
#                                 "type": "text_chunk",
#                                 "content": chunk
#                             }))
#                             full_response += chunk
                            
#                 except Exception as e:
#                     error_msg = f"Error generating response: {str(e)}"
#                     logger.error(error_msg)
#                     await websocket.send_text(json.dumps({
#                         "type": "error",
#                         "content": error_msg
#                     }))
#                     full_response = error_msg

#                 # Send end of response and sources
#                 await websocket.send_text(json.dumps({
#                     "type": "end",
#                     "content": "Response complete."
#                 }))
                
#                 if retrieved_source_ids:
#                     await websocket.send_text(json.dumps({
#                         "type": "sources",
#                         "content": retrieved_source_ids
#                     }))

#                 # Store the AI's response
#                 await create_message(
#                     supabase_client,
#                     conversation_id,
#                     "ai",
#                     full_response,
#                     retrieved_source_ids
#                 )
                
#             except WebSocketDisconnect:
#                 logger.info(f"Client disconnected: {user_id}")
#                 return
                
#             except Exception as e:
#                 error_msg = f"Error processing message: {str(e)}"
#                 logger.error(error_msg)
#                 await websocket.send_text(json.dumps({
#                     "type": "error",
#                     "content": error_msg
#                 }))

#     except WebSocketDisconnect:
#         logger.info(f"WebSocket disconnected for user {user_id}")
#         return
        
#     except ValueError as ve:
#         error_msg = f"Protocol error: {str(ve)}"
#         logger.error(error_msg)
#         try:
#             await websocket.send_text(json.dumps({
#                 "type": "error",
#                 "content": error_msg
#             }))
#             await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
#         except:
#             pass  # Connection already closed
            
#     except HTTPException as he:
#         error_msg = f"Authentication error: {he.detail}"
#         logger.error(error_msg)
#         try:
#             await websocket.send_text(json.dumps({
#                 "type": "error",
#                 "content": error_msg
#             }))
#             await websocket.close(code=he.status_code)
#         except:
#             pass  # Connection already closed
            
#     except Exception as e:
#         error_msg = f"Unexpected error: {str(e)}"
#         logger.error(error_msg)
#         try:
#             await websocket.send_text(json.dumps({
#                 "type": "error",
#                 "content": "An unexpected error occurred. Please try again."
#             }))
#             await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
#         except:
#             pass  # Connection already closed
    
#     finally:
#         # Clean up resources if needed
#         if 'supabase_client' in locals():
#             try:
#                 await supabase_client.auth.sign_out()
#             except:
#                 pass  # Ignore errors during cleanup


# app/api/v1/endpoints/chat.py (This replaces your WebSocket code)

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, List
from uuid import UUID
from app.schemas.rag import ChatMessagePayload, ChatResponse
from app.database.crud import (
    create_conversation,
    create_message,
    get_messages_by_conversation
)
from app.services.embedding_services import generate_embedding
from app.services.pinecone_services import query_pinecone
from app.services.rag_service import generate_rag_response_stream
from app.integrations.supabase_connect import get_supabase_client,set_supabase_rls_user_context
from app.core.config import settings
from supabase import Client
import json
import logging
from app.database.connection import get_mongo_db
from app.services.auth_services import get_current_user



# Assuming you've set up a logger
logger = logging.getLogger(__name__)
router = APIRouter()


# New REST API Endpoint
@router.post("/chat", response_model=ChatResponse)
async def chat_with_rag(
    payload: ChatMessagePayload,
    current_user: str = Depends(get_current_user),  # Authenticates from Authorization header
    supabase_client: Client = Depends(get_supabase_client),
    db = Depends(get_mongo_db),
    _rls_context: None = Depends(set_supabase_rls_user_context),
):
    """
    REST API endpoint to handle a single chat message with RAG capabilities.
    """
    # NOTE: The 'apply_rls_context' dependency should be implicitly included in your main router
    # or added here if you want to ensure the RLS is set for this call.
    # For now, let's assume it's applied at the router level.
    
    # --- Quota Check (MongoDB UsageMetrics) ---
    # Implement your quota check here if needed before processing the query.
    # E.g., user_metrics = await get_user_metrics_from_mongodb(user_id)
    # if user_metrics.rag_queries_this_month >= user_metrics.rag_queries_limit_monthly:
    #     raise HTTPException(status_code=403, detail="Monthly query limit exceeded.")

    try:
        print(f"Received chat request from user {current_user['_id']}: {payload}")
        collection_id_str = payload.collection_id
        conversation_id_uuid = None
        user_id = str(current_user['_id'])
        print("Handling conversation")
        # 1. Handle Conversation (create new or use existing)
        if payload.conversation_id:
            # TODO: Add logic to verify conversation belongs to user and collection
            conversation_id_uuid = payload.conversation_id
            print(f"Using existing conversation for user {user_id}: {conversation_id_uuid}")
        else:
            print(f"Creating new conversation for user {user_id} with collection {collection_id_str}")
            new_conv = create_conversation(supabase_client, user_id, collection_id_str)
            conversation_id_uuid = new_conv['id']
            print(f"New conversation started for user {user_id}: {conversation_id_uuid}")
        print("Storing user's message in conversation")
        # 2. Store the user's message
        create_message(
            supabase_client,
            conversation_id_uuid,
            "user",
            payload.query
        )
        print(f"Stored user message in conversation {conversation_id_uuid}")
        print("Getting relevant context using the query")
        # 3. Get relevant context using the query
        query_embedding = await generate_embedding(payload.query)
        print(f"Generated query embedding for user {user_id}: {query_embedding[:10]}...")
        print("Querying Pinecone")
        retrieved_matches = await query_pinecone(
            user_id=user_id,
            query_embedding=query_embedding,
            collection_id=UUID(collection_id_str),
            top_k=settings.TOP_K_RETRIEVAL
        )
        print(f"Retrieved {len(retrieved_matches)} relevant documents for user {user_id}")
        print("Extracting source IDs and content from matches")
        # 4. Extract source IDs and content from matches
        retrieved_source_ids = [
            match.id for match in retrieved_matches
            if hasattr(match, 'id') and match.id
        ]
        print(f"Retrieved source IDs: {retrieved_source_ids}")
        context_list = [
            {"content": match.metadata.get('content', '')}
            for match in retrieved_matches
            if match.metadata and match.metadata.get('content', '')
        ]
        print(f"Context list: {context_list}")
        print("Extracting source IDs and content from matches")
        # 5. Generate the LLM response
        full_response = ""
        try:
            # Note: The streaming function is a generator. We need to iterate it
            # and collect all the chunks into a single string.
            async for chunk in generate_rag_response_stream(
                user_id=user_id,
                query=payload.query,
                collection_id=UUID(collection_id_str),
                conversation_id=conversation_id_uuid,
                supabase_client=supabase_client,
            ):
                if isinstance(chunk, str):
                    full_response += chunk
                elif isinstance(chunk, dict) and 'data' in chunk:
                    full_response += chunk['data']
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            print(error_msg)
            full_response = error_msg
        print("Storing AI's response")
        # 6. Store the AI's response
        create_message(
            supabase_client,
            conversation_id_uuid,
            "ai",
            full_response,
            retrieved_source_ids
        )
        print(f"Stored AI response in conversation {conversation_id_uuid}")

        # 7. Return the final structured response
        return ChatResponse(
            conversation_id=str(conversation_id_uuid),
            ai_response=full_response,
            retrieved_sources=[str(s) for s in retrieved_source_ids]
        )

    except HTTPException:
        raise  # Re-raise FastAPI HTTP exceptions
    except Exception as e:
        error_msg = f"An unexpected error occurred: {str(e)}"
        print(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )