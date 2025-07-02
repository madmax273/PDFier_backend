from pydantic import BaseModel, Field
from bson import ObjectId
from datetime import datetime
from typing import Optional
from app.core.config import settings
from datetime import timedelta


class OTPModel(BaseModel):
    user_id: str = Field(..., description="User ID")
    otp: str = Field(..., description="One time password")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation time")
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=10),
                                 description="Expiration time")


class UsageMetrics(BaseModel):
    pdf_processed_today: int
    pdf_processed_limit_daily: int
    rag_queries_this_month: int
    rag_queries_limit_monthly: int
    rag_indexed_documents_count: int
    rag_indexed_documents_limit: int
    word_conversions_today: int
    word_conversions_limit_daily: int
    last_quota_reset_date: str # ISO format string 

class UserModel(BaseModel):
    name: str = Field(..., description="User name")
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")
    verified: bool = Field(False, description="Is user verified")
    ip_address: str = Field(..., description="User IP address")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Update time")
    plan_type: str = Field("basic", description="User plan type")
    usage_metrics: UsageMetrics = Field({}, description="User usage metrics")
