from typing import Optional, List
from fastapi import Depends, Request, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole, SessionToken
from app.models.merchant import Merchant, MerchantMembership
from app.core.security import decode_access_token
from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.config import settings


def get_token_from_request(request: Request, authorization: Optional[str] = Header(None)) -> Optional[str]:
    # 1. Bearer header
    if authorization and authorization.startswith("Bearer "):
        return authorization.split(" ")[1]
    # 2. HttpOnly Cookie
    cookie_token = request.cookies.get(settings.COOKIE_NAME)
    if cookie_token:
        return cookie_token
    return None


def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> User:
    token = get_token_from_request(request, authorization)
    if not token:
        raise AuthenticationError("Authentication token is missing. Please log in.")

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise AuthenticationError("Invalid or expired session token")

    user_id = payload["sub"]
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise AuthenticationError("User not found or account is deactivated")

    return user


def require_roles(*allowed_roles: UserRole):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise PermissionDeniedError(
                f"Role '{current_user.role.value}' is not permitted to access this resource. Allowed: {[r.value for r in allowed_roles]}"
            )
        return current_user
    return role_checker


require_customer = require_roles(UserRole.CUSTOMER, UserRole.ADMIN)
require_merchant = require_roles(UserRole.MERCHANT, UserRole.ADMIN)
require_admin = require_roles(UserRole.ADMIN)


def get_merchant_for_user(current_user: User = Depends(require_merchant), db: Session = Depends(get_db)) -> Optional[Merchant]:
    if current_user.role == UserRole.ADMIN:
        return None  # Admin has system-wide view
    if not current_user.merchant_memberships:
        raise PermissionDeniedError("User has no associated merchant account.")
    return current_user.merchant_memberships[0].merchant
