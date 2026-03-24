import asyncio
from app.services.embedding_services import generate_embedding
from app.core.config import settings
print("Model name from settings:", settings.EMBEDDING_MODEL_NAME)

async def test():
    emb = await generate_embedding("hello")
    print("Length of embedding:", len(emb))

asyncio.run(test())
