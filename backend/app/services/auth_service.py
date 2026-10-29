import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.user import User, SessionToken, UserRole
from app.schemas.auth import LoginRequest, RegisterCustomerRequest
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.exceptions import AuthenticationError, SwitchException
from app.services import audit_service


def authenticate_user(db: Session, data: LoginRequest) -> Tuple[User, str]:
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise AuthenticationError("Incorrect email or password")

    if not user.is_active:
        raise AuthenticationError("User account is inactive. Please contact system administrator.")

    token = create_access_token(data={"sub": user.id, "email": user.email, "role": user.role.value})

    session_token = SessionToken(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=120),
    )
    db.add(session_token)
    db.flush()

    audit_service.log_audit_event(
        db,
        action="USER_LOGIN",
        entity_type="USER",
        entity_id=user.id,
        user_id=user.id,
    )

    return user, token


def register_customer(db: Session, data: RegisterCustomerRequest) -> User:
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise SwitchException("USER_EXISTS", f"User with email '{data.email}' already exists")

    user = User(
        id=str(uuid.uuid4()),
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add(user)
    db.flush()

    audit_service.log_audit_event(
        db,
        action="CUSTOMER_REGISTERED",
        entity_type="USER",
        entity_id=user.id,
        user_id=user.id,
    )

    return user
