import google.generativeai as genai
from app.core.config import settings
genai.configure(api_key=settings.GOOGLE_API_KEY)
for model in genai.list_models():
    print(model.name)