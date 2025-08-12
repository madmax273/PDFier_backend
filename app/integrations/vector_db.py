import os
from pinecone import Pinecone, PodSpec, ServerlessSpec
from app.core.config import settings # Assuming this correctly imports your settings

# Initialize the Pinecone client at a global level (or within a function if preferred)
# We'll make this a global variable, similar to your original `pinecone_index` idea,
# but it will be the *Pinecone client instance*, not the Index directly.
pinecone_client: Pinecone = None
pinecone_index_instance = None # This will hold the specific index object

async def initialize_pinecone():
    global pinecone_client
    global pinecone_index_instance

    if not settings.PINECONE_API_KEY or not settings.PINECONE_ENVIRONMENT or not settings.PINECONE_INDEX_NAME:
        raise ValueError("Pinecone credentials or index name not found in environment variables.")

    try:
        # 1. Initialize the Pinecone client
        # For serverless indexes, 'environment' is often not strictly needed during client init,
        # but it's good practice to provide it if you have it set up for pod-based too.
        pinecone_client = Pinecone(api_key=settings.PINECONE_API_KEY, environment=settings.PINECONE_ENVIRONMENT)

        # 2. Check if index exists and create if not
        # Use pinecone_client.list_indexes() to get the list of index names
        existing_indexes = [index.name for index in pinecone_client.list_indexes()]

        if settings.PINECONE_INDEX_NAME not in existing_indexes:
            print(f"Pinecone index '{settings.PINECONE_INDEX_NAME}' not found. Creating it...")
            
            # Determine the spec based on your needs (Serverless vs. Pod)
            # You might want to make this configurable in your settings
            if settings.PINECONE_CLOUD_SPEC == "SERVERLESS": # Example of a setting
                spec_to_use = ServerlessSpec(cloud=settings.PINECONE_CLOUD, region=settings.PINECONE_REGION)
            else: # Assuming PodSpec by default if not serverless
                spec_to_use = PodSpec(environment=settings.PINECONE_ENVIRONMENT, pod_type="p1.x1", replicas=1) # Customize pod_type and replicas as needed

            pinecone_client.create_index(
                name=settings.PINECONE_INDEX_NAME,
                dimension=768, # <<< THIS IS CRITICAL - Must match text-embedding-004
                metric="cosine",
                spec=spec_to_use
            )
            print(f"Created Pinecone index '{settings.PINECONE_INDEX_NAME}'.")
        else:
            print(f"Pinecone index '{settings.PINECONE_INDEX_NAME}' already exists.")

        # 3. Connect to the specific index
        # Access the index object using the client
        pinecone_index_instance = pinecone_client.Index(name=settings.PINECONE_INDEX_NAME)
        print("✅ Pinecone client initialized successfully and connected to index.")
    except Exception as e:
        print(f"❌ Error initializing Pinecone client: {e}")
        raise RuntimeError(f"Failed to initialize Pinecone: {e}")

async def get_pinecone_index():
    """Returns the initialized Pinecone index instance."""
    if pinecone_index_instance is None:
        raise RuntimeError("Pinecone index not initialized. Call initialize_pinecone() first.")
    return pinecone_index_instance

# Example of how you might use it (for testing or understanding)
# if __name__ == "__main__":
#     # Dummy settings for demonstration. In real app, these come from app.core.config
#     class MockSettings:
#         PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "YOUR_API_KEY") # Replace or set env var
#         PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "YOUR_ENVIRONMENT") # e.g., "gcp-starter", "us-east-1-aws"
#         PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "my-test-index")
#         PINECONE_CLOUD_SPEC = os.getenv("PINECONE_CLOUD_SPEC", "SERVERLESS") # "SERVERLESS" or "POD"
#         PINECONE_CLOUD = os.getenv("PINECONE_CLOUD", "aws") # or 'gcp'
#         PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1") # e.g., 'us-central1' for GCP

#     settings = MockSettings() # Replace this with your actual settings import

#     import asyncio
#     async def main():
#         await initialize_pinecone()
#         index = await get_pinecone_index()
#         print(f"Index stats: {index.describe_index_stats()}")
#         # You can now perform operations like index.upsert, index.query, etc.

#     asyncio.run(main())