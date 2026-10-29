from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models.user import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: "UserResponse"


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    merchant_id: Optional[str] = None
    merchant_name: Optional[str] = None

    class Config:
        from_attributes = True


class RegisterCustomerRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
