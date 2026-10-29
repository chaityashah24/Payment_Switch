import pytest
from app.schemas.auth import LoginRequest, RegisterCustomerRequest
from app.services import auth_service
from app.core.exceptions import AuthenticationError
from app.core.security import decode_access_token


def test_auth_login_success(db, test_admin):
    req = LoginRequest(email=test_admin.email, password="AdminPass123")
    user, token = auth_service.authenticate_user(db, req)
    assert user.id == test_admin.id
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == test_admin.id
    assert payload["role"] == "ADMIN"


def test_auth_login_wrong_password_fails(db, test_admin):
    req = LoginRequest(email=test_admin.email, password="WrongPassword!")
    with pytest.raises(AuthenticationError):
        auth_service.authenticate_user(db, req)


def test_auth_register_customer(db):
    req = RegisterCustomerRequest(
        email="new_student@lntfintech.edu",
        password="SecureStudent123",
        full_name="Student Developer",
    )
    user = auth_service.register_customer(db, req)
    assert user.id is not None
    assert user.email == "new_student@lntfintech.edu"
    assert user.role.value == "CUSTOMER"
