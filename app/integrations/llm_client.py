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
