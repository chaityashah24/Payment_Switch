import pytest
import uuid
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from app.models.merchant import Merchant, MerchantMembership, MerchantStatus
from app.models.account import SimulatedBank, SimulatedAccount, PaymentInstrument, InstrumentType
from app.models.payment import PaymentRoute, PaymentMethod
from app.core.security import get_password_hash, create_access_token

# In-memory SQLite with StaticPool so all connections share the same memory database without locking!
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_admin(db: Session) -> User:
    user = User(
        id=str(uuid.uuid4()),
        email=f"admin_{uuid.uuid4().hex[:6]}@test.edu",
        hashed_password=get_password_hash("AdminPass123"),
        full_name="Test Administrator",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def test_customer(db: Session) -> User:
    user = User(
        id=str(uuid.uuid4()),
        email=f"customer_{uuid.uuid4().hex[:6]}@test.edu",
        hashed_password=get_password_hash("CustomerPass123"),
        full_name="Test Customer",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db.add(user)
    db.commit()

    bank = SimulatedBank(
        id=str(uuid.uuid4()),
        code=f"SIM_BANK_{uuid.uuid4().hex[:4].upper()}",
        name="Test Bank",
        ifsc_prefix="TEST",
        is_available=True,
    )
    db.add(bank)
    db.commit()

    acc = SimulatedAccount(
        id=str(uuid.uuid4()),
        user_id=user.id,
        bank_id=bank.id,
        account_number=f"ACC_{uuid.uuid4().hex[:8]}",
        account_type="SAVINGS",
        balance_paise=1000000,
        available_balance_paise=1000000,
        currency="INR",
    )
    db.add(acc)
    db.commit()

    route = PaymentRoute(
        id=str(uuid.uuid4()),
        payment_method=PaymentMethod.UPI,
        bank_id=bank.id,
        is_enabled=True,
        priority=1,
    )
    db.add(route)
    db.commit()

    return user


@pytest.fixture
def test_merchant(db: Session) -> Merchant:
    user = User(
        id=str(uuid.uuid4()),
        email=f"merchant_{uuid.uuid4().hex[:6]}@test.edu",
        hashed_password=get_password_hash("MerchantPass123"),
        full_name="Test Merchant Owner",
        role=UserRole.MERCHANT,
        is_active=True,
    )
    db.add(user)
    db.commit()

    merchant = Merchant(
        id=str(uuid.uuid4()),
        business_name=f"Test Merchant Store {uuid.uuid4().hex[:4]}",
        contact_email=user.email,
        business_category="RETAIL",
        settlement_account_ref="SIM_ACC_TEST_123",
        supported_methods="UPI,CARD,NEFT,RTGS",
        fee_percentage_bps=150,
        fee_flat_paise=100,
        status=MerchantStatus.APPROVED,
    )
    db.add(merchant)
    db.commit()

    membership = MerchantMembership(
        id=str(uuid.uuid4()),
        user_id=user.id,
        merchant_id=merchant.id,
        role_in_merchant="OWNER",
    )
    db.add(membership)
    db.commit()

    return merchant


def get_auth_headers(user: User) -> dict:
    token = create_access_token(data={"sub": user.id, "email": user.email, "role": user.role.value})
    return {"Authorization": f"Bearer {token}"}
