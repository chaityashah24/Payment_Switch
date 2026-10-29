import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.account import SimulatedAccount, PaymentInstrument, SimulatedBank, InstrumentType
from app.models.user import User
from app.schemas.account import (
    SimulatedAccountResponse,
    PaymentInstrumentResponse,
    PaymentInstrumentCreate,
    BankResponse,
)
from app.api.deps import get_current_user, require_customer
from app.core.exceptions import SwitchException

router = APIRouter(prefix="/accounts", tags=["Simulated Accounts & Instruments"])


@router.get("", response_model=List[SimulatedAccountResponse])
def get_my_accounts(
    customer: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    accounts = (
        db.query(SimulatedAccount)
        .filter(SimulatedAccount.user_id == customer.id)
        .all()
    )
    return accounts


@router.get("/instruments", response_model=List[PaymentInstrumentResponse])
def get_my_instruments(
    customer: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    return (
        db.query(PaymentInstrument)
        .filter(PaymentInstrument.user_id == customer.id, PaymentInstrument.is_active == True)
        .all()
    )


@router.post("/instruments", response_model=PaymentInstrumentResponse, status_code=status.HTTP_201_CREATED)
def register_instrument(
    data: PaymentInstrumentCreate,
    customer: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    # Mask identifier for privacy & educational compliance
    masked = data.identifier
    if data.instrument_type == InstrumentType.CARD_TOKEN:
        clean = data.identifier.replace(" ", "").replace("-", "")
        masked = f"**** **** **** {clean[-4:] if len(clean) >= 4 else '1234'}"
    elif data.instrument_type == InstrumentType.BANK_ACCOUNT:
        masked = f"A/C ****{data.identifier[-4:] if len(data.identifier) >= 4 else '9999'}"

    token = f"tok_{uuid.uuid4().hex[:12]}"
    instrument = PaymentInstrument(
        id=str(uuid.uuid4()),
        user_id=customer.id,
        bank_id=data.bank_id,
        instrument_type=data.instrument_type,
        masked_identifier=masked,
        token_ref=token,
        card_brand=data.card_brand or "RUPAY",
        expiry_month=data.expiry_month or 12,
        expiry_year=data.expiry_year or 2030,
        is_active=True,
    )
    db.add(instrument)
    db.commit()
    db.refresh(instrument)
    return instrument


@router.get("/banks", response_model=List[BankResponse])
def list_simulated_banks(db: Session = Depends(get_db)):
    return db.query(SimulatedBank).all()
