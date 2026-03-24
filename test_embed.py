import traceback
import asyncio
from app.services.embedding_services import generate_embedding

async def test():
    try:
        await generate_embedding('test chunk')
        print("Embedding generated successfully")
    except Exception as e:
        print("Failed to generate embedding:")
        traceback.print_exc()

asyncio.run(test())
