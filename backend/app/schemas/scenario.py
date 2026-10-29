from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ScenarioUpdateRequest(BaseModel):
    is_active: bool
    apply_to_next_only: Optional[bool] = False
    route_id: Optional[str] = None
    parameters: Optional[str] = None


class ScenarioResponse(BaseModel):
    id: str
    name: str
    description: str
    is_active: bool
    apply_to_next_only: bool
    route_id: Optional[str] = None
    parameters: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
