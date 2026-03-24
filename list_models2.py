import json
import google.generativeai as genai
from app.core.config import settings
with open("models_out.txt", "w") as f:
    try:
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        models = [m.name for m in genai.list_models() if "embedContent" in m.supported_generation_methods]
        f.write(json.dumps(models))
    except Exception as e:
        f.write("ERROR: " + str(e))
