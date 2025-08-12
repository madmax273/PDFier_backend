# app/services/embedding_service.py

import google.generativeai as genai
from google.generativeai import GenerativeModel
from typing import List
from app.core.config import settings
from openai import AsyncOpenAI # Keep import but don't initialize if only using Google

openai_client: AsyncOpenAI = None # Will remain None
google_gemini_model: GenerativeModel = None

def initialize_llm_clients():
    global google_gemini_model # Only need to globalize the one you're using
    if settings.GOOGLE_API_KEY:
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        google_gemini_model = genai.GenerativeModel(settings.LLM_MODEL_NAME) # Initialize chat model
        print("✅ Google Gemini client initialized.")
    else:
        # If you were using OpenAI, its initialization would go here.
        # But since you're using Google, this block might be empty or raise an error
        # if no LLM client is configured.
        print("Google Gemini API Key not found. Gemini client not initialized.")
        # Consider raising an error if an LLM is absolutely required for app startup
        # raise RuntimeError("No LLM API key provided. Cannot initialize LLM clients.")


