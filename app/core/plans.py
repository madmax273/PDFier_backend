# app/core/plans.py (or similar central location)
from datetime import datetime

USER_PLANS = {
    "guest": { # For unauthenticated users on frontend, not stored in DB
        "pdf_processed_limit_daily": 2,
        "rag_queries_limit_monthly": 3,
        "rag_indexed_documents_limit": 1,
        "word_conversions_limit_daily": 0,
    },
    "basic": { # Default for newly signed-up users
        "pdf_processed_limit_daily": 10,
        "rag_queries_limit_monthly": 50,
        "rag_indexed_documents_limit": 5,
        "word_conversions_limit_daily": 2,
    },
    "premium": {
        "pdf_processed_limit_daily": 9999, # Effectively unlimited
        "rag_queries_limit_monthly": 9999,
        "rag_indexed_documents_limit": 9999,
        "word_conversions_limit_daily": 9999,
    }
}

# Helper function to initialize usage metrics for a new user/plan
def get_initial_usage_metrics(plan_type: str) -> dict:
    metrics = USER_PLANS.get(plan_type, {}).copy() # Get limits for the plan
    metrics.update({
        "pdf_processed_today": 0,
        "rag_queries_this_month": 0,
        "rag_indexed_documents_count": 0,
        "word_conversions_today": 0,
        "last_quota_reset_date": datetime.utcnow().isoformat() # Store as ISO string
    })
    return metrics