from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import asyncio

# This client will be initialized once during application startup
# and closed during shutdown using FastAPI's lifespan events.
client: AsyncIOMotorClient = None # type: ignore

async def connect_to_mongo():
    """Connect to MongoDB and set the global client instance."""
    global client
    client = AsyncIOMotorClient(settings.MONGO_URI)
    print("✅ MongoDB connected!")

async def close_mongo_connection():
    """Close the MongoDB connection."""
    global client
    if client:
        client.close()
        print("❌ MongoDB disconnected!")

def get_mongo_db():
    """
    Dependency function to get the MongoDB database object.
    This will be used in path operations.
    """
    if client is None:
        # This should ideally not happen if lifespan events are set up correctly,
        # but it's a safeguard for direct dependency testing or misconfiguration.
        raise RuntimeError("MongoDB client is not initialized.")
    return client[settings.DB_NAME]

if __name__ == "__main__":
    asyncio.run(get_mongo_db())
