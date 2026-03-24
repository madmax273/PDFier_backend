import asyncio
import traceback
from app.services.embedding_services import generate_embedding
from app.services.pinecone_services import upsert_vectors_to_pinecone
from app.integrations.vector_db import initialize_pinecone

async def test():
    try:
        print("Initializing Pinecone...")
        await initialize_pinecone()
        print("Generating embedding...")
        chunk_text = "This is a test document."
        embedding = await generate_embedding(chunk_text)
        print("Embedding generated, length:", len(embedding))

        vector_data = {
            "id": "test-vector-id-1234",
            "values": embedding,
            "metadata": {"content": chunk_text}
        }
        
        print("Upserting to Pinecone...")
        await upsert_vectors_to_pinecone("test-user-id", [vector_data])
        print("Upsert successful!")
    except Exception as e:
        print("Failed:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
