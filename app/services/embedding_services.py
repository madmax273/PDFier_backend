# app/services/embedding_service.py

from openai import AsyncOpenAI # pip install openai
import google.generativeai as genai
from google.generativeai import GenerativeModel, configure # pip install google-generativeai
from typing import List, Optional
from app.core.config import settings
import logging
from app.integrations.llm_client import initialize_llm_clients


logger = logging.getLogger(__name__)

# Initialize clients
openai_client: AsyncOpenAI = None # Will remain None
google_gemini_model: GenerativeModel = None

def initialize_llm_clients():
    global google_gemini_model # Only need to globalize the one you're using
    if settings.GOOGLE_API_KEY:
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        
        # Check generated content model availability dynamically
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Format the configured model 
        configured_model = settings.LLM_MODEL_NAME
        if not configured_model.startswith("models/"):
             configured_model = f"models/{configured_model}"
             
        eval_model = settings.LLM_MODEL_NAME
        if configured_model not in available_models:
             # Fallback to the first available chat model, preferring flash models
             flash_models = [m for m in available_models if "flash" in m]
             if flash_models:
                 eval_model = flash_models[0].replace("models/", "") 
             elif available_models:
                 eval_model = available_models[0].replace("models/", "")
             print(f"Configured model {settings.LLM_MODEL_NAME} not found. Falling back to {eval_model}")

        google_gemini_model = genai.GenerativeModel(eval_model) # Initialize chat model
        print(f" Google Gemini client initialized with model: {eval_model}.")
    else:
        # If you were using OpenAI, its initialization would go here.
        # But since you're using Google, this block might be empty or raise an error
        # if no LLM client is configured.
        print("Google Gemini API Key not found. Gemini client not initialized.")

# Initialize clients when module is imported
initialize_llm_clients()

async def generate_embedding(text: str) -> List[float]:
    """
    Generates an embedding for the given text using the configured model.
    
    Args:
        text: The input text to generate embedding for
        
    Returns:
        List[float]: The embedding vector
        
    Raises:
        RuntimeError: If embedding generation fails
        ValueError: If the model is not supported or clients are not initialized
    """
    if not text.strip():
        raise ValueError("Input text cannot be empty")
    
    # OpenAI models
    if settings.EMBEDDING_MODEL_NAME in ["text-embedding-ada-002", "text-embedding-3-small", "text-embedding-3-large"]:
        if not openai_client:
            raise ValueError("OpenAI client not initialized. Check your API key.")
            
        try:
            response = await openai_client.embeddings.create(
                input=text,
                model=settings.EMBEDDING_MODEL_NAME
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating OpenAI embedding: {e}")
            raise RuntimeError(f"Failed to generate embedding: {e}")
    
    # Google models
    elif ("embedding" in settings.EMBEDDING_MODEL_NAME) and settings.GOOGLE_API_KEY:
        if not google_gemini_model:
            raise ValueError("Google Gemini client not initialized. Check your API key.")
            
        try:
            import google.generativeai as genai
            
            # Find an available embedding model dynamically
            available_models = [m.name for m in genai.list_models() if 'embedContent' in m.supported_generation_methods]
            eval_model = available_models[0] if available_models else "models/text-embedding-004"

            # If the user-specified model is actually valid, we optionally could use it, 
            # but let's just safely use the first available one to prevent 404s.
            if settings.EMBEDDING_MODEL_NAME in available_models:
                eval_model = settings.EMBEDDING_MODEL_NAME

            result = genai.embed_content(
                model=eval_model,
                content=text,
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=768
            )
            return result["embedding"]
        except Exception as e:
            logger.error(f"Error generating Google embedding: {e}")
            raise RuntimeError(f"Failed to generate embedding: {e}")
    
    # Unsupported model
    else:
        raise ValueError(
            f"Unsupported embedding model: {settings.EMBEDDING_MODEL_NAME}. "
            "Supported models are: text-embedding-ada-002, text-embedding-3-small, "
            "text-embedding-3-large, text-embedding-004, or Google's models/embedding-*"
        )

async def get_llm_completion_stream(prompt: str):
    """Generates a streaming response from the configured LLM."""
    if settings.LLM_MODEL_NAME.startswith("gpt") and openai_client:
        try:
            stream = await openai_client.chat.completions.create(
                model=settings.LLM_MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions concisely and accurately based on provided context."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                stream=True
            )
            async for chunk in stream:
                yield chunk.choices[0].delta.content or ""
        except Exception as e:
            print(f"Error streaming OpenAI LLM response: {e}")
            yield "[ERROR] Could not generate response."
    elif settings.LLM_MODEL_NAME.startswith("gemini") and google_gemini_model:
        try:
            # Assuming google_gemini_model is already configured with API key
            response_stream = google_gemini_model.generate_content(
                prompt,
                stream=True,
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
            )
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            print(f"Error streaming Google Gemini LLM response: {e}")
            yield "[ERROR] Could not generate response."
    else:
        raise ValueError(f"Unsupported LLM model or client not initialized: {settings.LLM_MODEL_NAME}")

# Call this in your lifespan to initialize clients
# This should be called *after* settings are loaded
# In main.py, import initialize_llm_clients and call it in lifespan.