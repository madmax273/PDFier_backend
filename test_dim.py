import traceback
import google.generativeai as genai
from app.core.config import settings
import asyncio

async def test():
    try:
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        models = [m.name for m in genai.list_models() if "embedContent" in m.supported_generation_methods]
        
        for eval_model in models:
            try:
                print(f"Testing {eval_model}")
                result = genai.embed_content(
                    model=eval_model,
                    content="Hello world",
                    task_type="RETRIEVAL_DOCUMENT",
                    output_dimensionality=768
                )
                print(f"Success for {eval_model}! Output length: {len(result['embedding'])}")
            except Exception as e:
                print(f"Failed for {eval_model}: {e}")

    except Exception as e:
        print("Global Error:")
        traceback.print_exc()

asyncio.run(test())
