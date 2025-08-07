from pydantic_settings import BaseSettings  
from typing import List, Optional
import os
from urllib.parse import quote_plus

class Settings(BaseSettings):
    PROJECT_NAME: str = "PDFier API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # MongoDB settings 
    MONGO_USER: str
    MONGO_PASS: str
    MONGO_CLUSTER: str
    DB_NAME: str
   

    @property
    def MONGO_URI(self):
        user = quote_plus(self.MONGO_USER)
        passwd = quote_plus(self.MONGO_PASS)
        return f"mongodb+srv://{user}:{passwd}@{self.MONGO_CLUSTER}/{self.DB_NAME}?retryWrites=true&w=majority"


    # JWT settings
    SECRET_KEY: str  
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int 
    REFRESH_TOKEN_EXPIRE_DAYS: int 
    JWT_REFRESH_SECRET_KEY: str
    
    # CORS settings
    # BACKEND_CORS_ORIGINS: List[str] = []

    # Email settings
    EMAIL_USER: str
    EMAIL_PASS: str

    # Firebase settings
    # SERVICE_ACCOUNT_KEY_PATH: str
    # FIREBASE_STORAGE_BUCKET: str
    # FIREBASE_SERVICE_ACCOUNT_KEY_JSON: str

    # Supabase settings
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_PDF_BUCKET_NAME: str

    # OpenAI / Gemini API Key (choose one or configure both)
    OPENAI_API_KEY: str = None # Set to None or empty string if not using OpenAI
    GOOGLE_API_KEY: str = None # Set to None or empty string if not using Google Gemini

    # LLM and Embedding Model Names
    LLM_MODEL_NAME: str = "gpt-3.5-turbo" # or "gemini-pro" or other
    EMBEDDING_MODEL_NAME: str = "text-embedding-ada-002" # or "text-embedding-004" or "sentence-transformers/all-MiniLM-L6-v2"

    # Pinecone Settings
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str # e.g., "us-east-1"
    PINECONE_INDEX_NAME: str = "pdf-rag-index" # Name of your Pinecone index

    # RAG Configuration
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RETRIEVAL: int = 5 # Number of top relevant chunks to retrieve
    CONVERSATION_HISTORY_LIMIT: int = 5 # Number of messages to include in conversation history

    class Config:
        env_file = ".env"

settings = Settings()
