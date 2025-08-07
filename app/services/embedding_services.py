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
        google_gemini_model = genai.GenerativeModel(settings.LLM_MODEL_NAME) # Initialize chat model
        print(" Google Gemini client initialized.")
    else:
        # If you were using OpenAI, its initialization would go here.
        # But since you're using Google, this block might be empty or raise an error
        # if no LLM client is configured.
        print("Google Gemini API Key not found. Gemini client not initialized.")
        # Consider raising an error if an LLM is absolutely required for app startup
        # raise RuntimeError("No LLM API key provided. Cannot initialize LLM clients.")

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
    elif settings.EMBEDDING_MODEL_NAME.startswith("models/embedding-") and settings.GOOGLE_API_KEY:
        if not google_gemini_model:
            raise ValueError("Google Gemini client not initialized. Check your API key.")
            
        try:
            import google.generativeai as genai
            result = genai.embed_content(
                model=settings.EMBEDDING_MODEL_NAME,
                content=text,
                task_type="RETRIEVAL_DOCUMENT"
            )
            print(result)
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
                stream=False,
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
            )
            for chunk in response_stream:
                yield chunk.text
        except Exception as e:
            print(f"Error streaming Google Gemini LLM response: {e}")
            yield "[ERROR] Could not generate response."
    else:
        raise ValueError(f"Unsupported LLM model or client not initialized: {settings.LLM_MODEL_NAME}")

# Call this in your lifespan to initialize clients
# This should be called *after* settings are loaded
# In main.py, import initialize_llm_clients and call it in lifespan.