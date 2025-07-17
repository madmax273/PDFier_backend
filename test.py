import os
from supabase import create_client, Client
from app.core.config import settings
# --- Configuration ---
# It's best practice to load these from environment variables
# url: str = os.environ.get("SUPABASE_URL")
# key: str = os.environ.get("SUPABASE_ANON_KEY")

# For a quick test, you can paste them directly:
SUPABASE_URL=settings.SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY=settings.SUPABASE_SERVICE_ROLE_KEY
SUPABASE_PDF_BUCKET_NAME=settings.SUPABASE_PDF_BUCKET_NAME

# --- Initialization ---
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
print(f"Checking status for bucket: '{SUPABASE_PDF_BUCKET_NAME}'...")

# --- Check Bucket Status ---
try:
    # This returns a 'Bucket' object
    res = supabase.storage.get_bucket(SUPABASE_PDF_BUCKET_NAME)

    # Access the 'public' attribute directly using dot notation
    if res.public:
        print(f"✅ The bucket '{SUPABASE_PDF_BUCKET_NAME}' is public.")
    else:
        print(f"🔒 The bucket '{SUPABASE_PDF_BUCKET_NAME}' is private.")

except Exception as e:
    print(f"❌ Error checking bucket '{SUPABASE_PDF_BUCKET_NAME}': {e}")

# # --- Initialization ---
# supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
# print(f"Attempting to make bucket '{SUPABASE_PDF_BUCKET_NAME}' public...")

# # --- Update Bucket ---
# try:
#     # Set the 'public' option to True for the specified bucket
#     res = supabase.storage.update_bucket(
#         SUPABASE_PDF_BUCKET_NAME,
#         {"public": True}
#     )
#     print(f"✅ Success: Bucket '{SUPABASE_PDF_BUCKET_NAME}' is now public.")

# except Exception as e:
#     print(f"❌ Error updating bucket: {e}")