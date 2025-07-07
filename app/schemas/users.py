from pydantic import BaseModel, Field
from datetime import datetime
from app.database.models import UsageMetrics


class UserOut(BaseModel):
    name: str = Field(..., description="User name")
    verified: bool = Field(False, description="Is user verified")
    ip_address: str = Field(..., description="User IP address")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Update time")
    plan_type: str = Field("basic", description="User plan type")
    usage_metrics: UsageMetrics = Field({}, description="User usage metrics")