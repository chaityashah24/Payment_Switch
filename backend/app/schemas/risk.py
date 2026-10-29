from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.risk import RiskRuleType, RiskAction


class RiskRuleCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str = Field(..., max_length=255)
    rule_type: RiskRuleType
    threshold_value: int = Field(..., description="Paise amount or attempt count")
    window_seconds: int = Field(default=300, ge=10)
    action: RiskAction = RiskAction.REVIEW
    is_active: bool = True


class RiskRuleResponse(BaseModel):
    id: str
    name: str
    description: str
    rule_type: RiskRuleType
    threshold_value: int
    window_seconds: int
    action: RiskAction
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RiskDecisionResponse(BaseModel):
    id: str
    payment_id: str
    risk_rule_id: Optional[str] = None
    action: RiskAction
    reason: str
    resolution_action: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RiskReviewResolveRequest(BaseModel):
    action: str = Field(..., description="APPROVE or DECLINE")
    notes: Optional[str] = None
