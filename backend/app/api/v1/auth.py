from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse, RegisterCustomerRequest
from app.models.user import User
from app.services import auth_service
from app.api.deps import get_current_user
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user, token = auth_service.authenticate_user(db, data)
    
    # Set HttpOnly cookie
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )

    merchant_id = None
    merchant_name = None
    if user.merchant_memberships:
        merchant_id = user.merchant_memberships[0].merchant_id
        merchant_name = user.merchant_memberships[0].merchant.business_name

    user_resp = UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        merchant_id=merchant_id,
        merchant_name=merchant_name,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=user_resp,
    )


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=settings.COOKIE_NAME)
    return {"message": "Successfully logged out of simulation session"}


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(user: User = Depends(get_current_user)):
    merchant_id = None
    merchant_name = None
    if user.merchant_memberships:
        merchant_id = user.merchant_memberships[0].merchant_id
        merchant_name = user.merchant_memberships[0].merchant.business_name

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        merchant_id=merchant_id,
        merchant_name=merchant_name,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterCustomerRequest, db: Session = Depends(get_db)):
    user = auth_service.register_customer(db, data)
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )
