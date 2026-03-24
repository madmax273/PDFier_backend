import asyncio
import traceback
from app.core.config import settings
from app.services.embedding_services import google_gemini_model

async def test():
    try:
        print("Testing chat stream...")
        response_stream = google_gemini_model.generate_content(
            "Say hello",
            stream=True,
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        )
        for chunk in response_stream:
             print("Chunk:", chunk.text)
        print("Done")
    except Exception as e:
        print("Failed:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
