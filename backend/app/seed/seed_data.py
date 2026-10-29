import uuid
import json
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal, Base, engine
from app.models.user import User, UserRole
from app.models.merchant import Merchant, MerchantMembership, MerchantStatus
from app.models.account import SimulatedBank, SimulatedAccount, PaymentInstrument, InstrumentType
from app.models.payment import Payment, PaymentStatus, PaymentMethod, PaymentRoute
from app.models.refund import Refund, RefundStatus
from app.models.settlement import SettlementBatch, SettlementItem, BatchStatus, SettlementItemStatus, SettlementAllocation
from app.models.reconciliation import ReconciliationRun, ReconciliationException, RecRunStatus, RecExceptionType, RecExceptionSeverity, RecExceptionStatus
from app.models.risk import RiskRule, RiskRuleType, RiskAction
from app.models.scenario import SimulationScenario
from app.core.security import get_password_hash
from app.services import ledger_service, payment_service


def seed_database():
    db = SessionLocal()
    try:
        print("[SEED] Seeding Secure Payment Switch database...")

        # 1. Administrator
        admin = db.query(User).filter(User.email == "admin@lntfintech.edu").first()
        if not admin:
            admin = User(
                id=str(uuid.uuid4()),
                email="admin@lntfintech.edu",
                hashed_password=get_password_hash("Admin@12345"),
                full_name="Dr. S. K. Narayanan (System Admin)",
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin)

        # 2. Merchants & Users
        m1_user = db.query(User).filter(User.email == "merchant.acme@lntfintech.edu").first()
        if not m1_user:
            m1_user = User(
                id=str(uuid.uuid4()),
                email="merchant.acme@lntfintech.edu",
                hashed_password=get_password_hash("Merchant@12345"),
                full_name="Acme Retail Operations",
                role=UserRole.MERCHANT,
                is_active=True,
            )
            db.add(m1_user)

        m2_user = db.query(User).filter(User.email == "merchant.nova@lntfintech.edu").first()
        if not m2_user:
            m2_user = User(
                id=str(uuid.uuid4()),
                email="merchant.nova@lntfintech.edu",
                hashed_password=get_password_hash("Merchant@12345"),
                full_name="Nova Digital Services",
                role=UserRole.MERCHANT,
                is_active=True,
            )
            db.add(m2_user)

        db.flush()

        # Merchant entities
        m1 = db.query(Merchant).filter(Merchant.business_name == "Acme Electronics & Retail").first()
        if not m1:
            m1 = Merchant(
                id="mch_acme_electronics_01",
                business_name="Acme Electronics & Retail",
                contact_email="merchant.acme@lntfintech.edu",
                business_category="E-COMMERCE",
                settlement_account_ref="SIM_HDFC_9988776655",
                supported_methods="UPI,CARD,NEFT,RTGS",
                fee_percentage_bps=150,  # 1.50%
                fee_flat_paise=0,
                status=MerchantStatus.APPROVED,
                approved_at=datetime.now(timezone.utc),
            )
            db.add(m1)
            db.flush()
            db.add(MerchantMembership(
                id=str(uuid.uuid4()),
                user_id=m1_user.id,
                merchant_id=m1.id,
                role_in_merchant="OWNER",
            ))

        m2 = db.query(Merchant).filter(Merchant.business_name == "Nova Cloud Subscriptions").first()
        if not m2:
            m2 = Merchant(
                id="mch_nova_cloud_02",
                business_name="Nova Cloud Subscriptions",
                contact_email="merchant.nova@lntfintech.edu",
                business_category="SAAS",
                settlement_account_ref="SIM_ICICI_1122334455",
                supported_methods="UPI,CARD,NEFT,RTGS",
                fee_percentage_bps=200,  # 2.00%
                fee_flat_paise=500,     # ₹5 flat fee
                status=MerchantStatus.APPROVED,
                approved_at=datetime.now(timezone.utc),
            )
            db.add(m2)
            db.flush()
            db.add(MerchantMembership(
                id=str(uuid.uuid4()),
                user_id=m2_user.id,
                merchant_id=m2.id,
                role_in_merchant="OWNER",
            ))

        # Pending Merchant (for admin approval demonstration)
        m3 = db.query(Merchant).filter(Merchant.business_name == "Apex Retail Ventures (Pending)").first()
        if not m3:
            m3 = Merchant(
                id="mch_apex_pending_03",
                business_name="Apex Retail Ventures (Pending)",
                contact_email="onboarding@apexventures.demo",
                business_category="RETAIL",
                settlement_account_ref="SIM_SBI_3344556677",
                supported_methods="UPI,CARD",
                fee_percentage_bps=175,
                fee_flat_paise=200,
                status=MerchantStatus.PENDING,
            )
            db.add(m3)

        # 3. Customers
        c1 = db.query(User).filter(User.email == "customer1@lntfintech.edu").first()
        if not c1:
            c1 = User(
                id=str(uuid.uuid4()),
                email="customer1@lntfintech.edu",
                hashed_password=get_password_hash("Customer@12345"),
                full_name="Rahul Sharma",
                role=UserRole.CUSTOMER,
                is_active=True,
            )
            db.add(c1)

        c2 = db.query(User).filter(User.email == "customer2@lntfintech.edu").first()
        if not c2:
            c2 = User(
                id=str(uuid.uuid4()),
                email="customer2@lntfintech.edu",
                hashed_password=get_password_hash("Customer@12345"),
                full_name="Priya Patel",
                role=UserRole.CUSTOMER,
                is_active=True,
            )
            db.add(c2)

        db.flush()

        # 4. Simulated Banks
        banks_data = [
            ("SIM_HDFC", "Simulated HDFC Bank Ltd.", "HDFC", 45),
            ("SIM_ICICI", "Simulated ICICI Bank Ltd.", "ICIC", 50),
            ("SIM_SBI", "Simulated State Bank of India", "SBIN", 65),
            ("SIM_AXIS", "Simulated Axis Bank Ltd.", "UTIB", 40),
        ]
        bank_map = {}
        for code, name, ifsc, latency in banks_data:
            b = db.query(SimulatedBank).filter(SimulatedBank.code == code).first()
            if not b:
                b = SimulatedBank(
                    id=str(uuid.uuid4()),
                    code=code,
                    name=name,
                    ifsc_prefix=ifsc,
                    is_available=True,
                    latency_ms=latency,
                )
                db.add(b)
                db.flush()
            bank_map[code] = b

        # 5. Simulated Accounts & Opening Balances
        acc1 = db.query(SimulatedAccount).filter(SimulatedAccount.user_id == c1.id).first()
        if not acc1:
            acc1 = SimulatedAccount(
                id=str(uuid.uuid4()),
                user_id=c1.id,
                bank_id=bank_map["SIM_HDFC"].id,
                account_number="50100492817263",
                account_type="SAVINGS",
                balance_paise=5000000,           # ₹50,000.00
                available_balance_paise=5000000,
                currency="INR",
            )
            db.add(acc1)

        acc2 = db.query(SimulatedAccount).filter(SimulatedAccount.user_id == c2.id).first()
        if not acc2:
            acc2 = SimulatedAccount(
                id=str(uuid.uuid4()),
                user_id=c2.id,
                bank_id=bank_map["SIM_ICICI"].id,
                account_number="00110592817456",
                account_type="SAVINGS",
                balance_paise=7500000,           # ₹75,000.00
                available_balance_paise=7500000,
                currency="INR",
            )
            db.add(acc2)

        db.flush()

        # 6. Payment Instruments
        instruments_data = [
            (c1.id, InstrumentType.UPI_VPA, "rahul@okaxis", "tok_upi_rahul_01", None, None),
            (c1.id, InstrumentType.CARD_TOKEN, "**** **** **** 4242", "tok_card_visa_4242", 10, 2029),
            (c2.id, InstrumentType.UPI_VPA, "priya@simicici", "tok_upi_priya_02", None, None),
            (c2.id, InstrumentType.CARD_TOKEN, "**** **** **** 5555", "tok_card_mc_5555", 8, 2028),
        ]
        for u_id, itype, masked, tok, exp_m, exp_y in instruments_data:
            inst = db.query(PaymentInstrument).filter(PaymentInstrument.token_ref == tok).first()
            if not inst:
                inst = PaymentInstrument(
                    id=str(uuid.uuid4()),
                    user_id=u_id,
                    instrument_type=itype,
                    masked_identifier=masked,
                    token_ref=tok,
                    card_brand="VISA" if "visa" in tok else "MASTERCARD" if "mc" in tok else None,
                    expiry_month=exp_m,
                    expiry_year=exp_y,
                    is_active=True,
                )
                db.add(inst)

        # 7. Payment Routes
        routes_data = [
            (PaymentMethod.UPI, "SIM_HDFC", 1, 0),
            (PaymentMethod.UPI, "SIM_ICICI", 2, 0),
            (PaymentMethod.CARD, "SIM_HDFC", 1, 10),
            (PaymentMethod.CARD, "SIM_AXIS", 2, 10),
            (PaymentMethod.NEFT, "SIM_SBI", 1, 5),
            (PaymentMethod.RTGS, "SIM_SBI", 1, 15),
        ]
        for method, b_code, prio, fee in routes_data:
            b_id = bank_map[b_code].id
            rt = db.query(PaymentRoute).filter(PaymentRoute.payment_method == method, PaymentRoute.bank_id == b_id).first()
            if not rt:
                rt = PaymentRoute(
                    id=str(uuid.uuid4()),
                    payment_method=method,
                    bank_id=b_id,
                    is_enabled=True,
                    priority=prio,
                    fee_bps=fee,
                )
                db.add(rt)

        # 8. 13 Simulation Scenarios
        scenarios = [
            ("SUCCESS", "Standard successful end-to-end authorization and capture", False),
            ("INSUFFICIENT_FUNDS", "Simulated customer account or card limit insufficient", False),
            ("INVALID_DEMO_AUTH", "Simulated MPIN or 3DS verification challenge failure", False),
            ("BANK_UNAVAILABLE", "Simulated core banking switch returns HTTP 503 gateway outage", False),
            ("SLOW_RESPONSE", "Simulated network degradation with 800ms bank latency", False),
            ("TIMEOUT_BEFORE_PROCESSING", "Simulated timeout before reaching bank core", False),
            ("TIMEOUT_AFTER_BANK_SUCCESS", "Bank succeeds, but acknowledgment lost in transit (unknown outcome)", False),
            ("DUPLICATE_EVENT", "Simulated replay or duplicate bank webhook arrival", False),
            ("RISK_REVIEW", "Transaction flagged by risk rules for administrative review", False),
            ("RECONCILIATION_MISSING_RECORD", "Bank core drops transaction record to demonstrate missing-record exception", False),
            ("RECONCILIATION_AMOUNT_MISMATCH", "Bank core records ₹50 discrepancy to demonstrate amount-mismatch exception", False),
            ("RECONCILIATION_STATUS_MISMATCH", "Bank records SUCCESS while switch recorded DECLINED", False),
            ("SETTLEMENT_PAYOUT_FAILURE", "Simulated nodal payout API failure during merchant settlement batch", False),
        ]
        for name, desc, active in scenarios:
            sc = db.query(SimulationScenario).filter(SimulationScenario.name == name).first()
            if not sc:
                sc = SimulationScenario(
                    id=str(uuid.uuid4()),
                    name=name,
                    description=desc,
                    is_active=active,
                )
                db.add(sc)

        # 9. Risk Rules
        risk_rules = [
            ("Rule 1: High Transaction Value Limit", "Flag payments above ₹50,000 for manual compliance review", RiskRuleType.MAX_AMOUNT, 5000000, 0, RiskAction.REVIEW),
            ("Rule 2: Anti-Carding Velocity Check", "Block customers with more than 5 payments in 60 seconds", RiskRuleType.VELOCITY_WINDOW, 5, 60, RiskAction.DECLINE),
            ("Rule 3: Repeated Merchant Payment Alert", "Review more than 3 payments to same merchant within 120 seconds", RiskRuleType.REPEATED_MERCHANT, 3, 120, RiskAction.REVIEW),
        ]
        for name, desc, rtype, thresh, win, act in risk_rules:
            rr = db.query(RiskRule).filter(RiskRule.name == name).first()
            if not rr:
                rr = RiskRule(
                    id=str(uuid.uuid4()),
                    name=name,
                    description=desc,
                    rule_type=rtype,
                    threshold_value=thresh,
                    window_seconds=win,
                    action=act,
                    is_active=True,
                )
                db.add(rr)

        db.commit()

        # 10. Create Sample Transactions (UPI, Card, NEFT, RTGS)
        print("[SEED] Seeding sample payment transactions...")
        sample_payments = [
            (c1, m1.id, PaymentMethod.UPI, 250000, "rahul@okaxis", "ORD-ACME-001", "IDEMP-SEED-01", "PIN_1234"),
            (c1, m1.id, PaymentMethod.CARD, 120000, "tok_card_visa_4242", "ORD-ACME-002", "IDEMP-SEED-02", "3DS_SUCCESS"),
            (c2, m2.id, PaymentMethod.UPI, 49900, "priya@simicici", "ORD-NOVA-001", "IDEMP-SEED-03", "PIN_1234"),
            (c2, m1.id, PaymentMethod.RTGS, 2500000, "tok_upi_priya_02", "ORD-ACME-003", "IDEMP-SEED-04", None),
        ]
        created_payments = []
        for cust, m_id, meth, amt, inst, ord_ref, idemp, auth_tok in sample_payments:
            p = db.query(Payment).filter(Payment.idempotency_key == idemp).first()
            if not p:
                p = payment_service.initiate_payment(
                    db=db,
                    customer=cust,
                    merchant_id=m_id,
                    payment_method=meth,
                    amount_paise=amt,
                    instrument_ref=inst,
                    idempotency_key=idemp,
                    merchant_order_ref=ord_ref,
                    demo_auth_token=auth_tok,
                )
                db.commit()
            created_payments.append(p)

        # 11. Create a partial refund on payment 1
        print("[SEED] Seeding sample refund...")
        p1 = created_payments[0]
        if p1 and p1.status == PaymentStatus.SUCCEEDED:
            existing_ref = db.query(Refund).filter(Refund.payment_id == p1.id).first()
            if not existing_ref:
                from app.services import refund_service
                refund_service.create_refund(
                    db=db,
                    merchant_user=m1_user,
                    payment_id=p1.id,
                    amount_paise=50000,  # ₹500 partial refund
                    reason="Customer returned damaged electronic item",
                    idempotency_key="REF-SEED-IDEMP-01",
                )
                db.commit()

        # 12. Create a settled batch and a failed payout ready for retry
        print("[SEED] Seeding sample settlement batches...")
        existing_batch = db.query(SettlementBatch).first()
        if not existing_batch:
            # Create a completed batch for historical demonstration
            batch = SettlementBatch(
                id=str(uuid.uuid4()),
                batch_reference="SETTLE-BATCH-DEMO-HISTORIC",
                cutoff_timestamp=datetime.now(timezone.utc) - timedelta(days=1),
                status=BatchStatus.COMPLETED,
                total_gross_paise=1000000,
                total_fee_paise=15000,
                total_refund_adjustment_paise=50000,
                total_net_paise=935000,
                completed_at=datetime.now(timezone.utc) - timedelta(days=1),
            )
            db.add(batch)
            db.flush()

            # Item 1: Paid item
            db.add(SettlementItem(
                id=str(uuid.uuid4()),
                settlement_batch_id=batch.id,
                merchant_id=m1.id,
                gross_amount_paise=1000000,
                fee_amount_paise=15000,
                refund_amount_paise=50000,
                net_payable_paise=935000,
                payout_reference=f"PAYOUT-PAID-{uuid.uuid4().hex[:6].upper()}",
                status=SettlementItemStatus.PAID,
            ))

            # Item 2: Failed item ready for retry
            failed_batch = SettlementBatch(
                id=str(uuid.uuid4()),
                batch_reference="SETTLE-BATCH-DEMO-RETRY-READY",
                cutoff_timestamp=datetime.now(timezone.utc),
                status=BatchStatus.PARTIALLY_FAILED,
                total_gross_paise=500000,
                total_fee_paise=10000,
                total_refund_adjustment_paise=0,
                total_net_paise=490000,
            )
            db.add(failed_batch)
            db.flush()

            failed_item = SettlementItem(
                id="item_failed_ready_for_retry_01",
                settlement_batch_id=failed_batch.id,
                merchant_id=m2.id,
                gross_amount_paise=500000,
                fee_amount_paise=10000,
                refund_amount_paise=0,
                net_payable_paise=490000,
                payout_reference="PAYOUT-FAILED-DEMO-RETRY",
                status=SettlementItemStatus.FAILED,
                retry_count=0,
                last_error="Beneficiary account SIM_ICICI_1122334455 temporarily rejected transfer: Host timeout",
            )
            db.add(failed_item)
            db.commit()

        # 13. Create sample reconciliation run with exceptions
        print("[SEED] Seeding sample reconciliation exceptions...")
        existing_rec = db.query(ReconciliationRun).first()
        if not existing_rec:
            rec_run = ReconciliationRun(
                id="rec_run_demo_01",
                run_reference="REC-RUN-DEMO-01",
                period_start=datetime.now(timezone.utc) - timedelta(days=2),
                period_end=datetime.now(timezone.utc),
                status=RecRunStatus.COMPLETED,
                total_switch_records=4,
                total_bank_records=4,
                total_matched=3,
                total_exceptions=2,
                completed_at=datetime.now(timezone.utc),
            )
            db.add(rec_run)
            db.flush()

            # Exception 1: Amount mismatch
            db.add(ReconciliationException(
                id=str(uuid.uuid4()),
                reconciliation_run_id=rec_run.id,
                exception_type=RecExceptionType.AMOUNT_MISMATCH,
                severity=RecExceptionSeverity.HIGH,
                status=RecExceptionStatus.OPEN,
                reference_key="UPI-REC-DISC-01",
                explanation="Amount discrepancy detected: Switch recorded ₹1,200.00, Bank core recorded ₹1,150.00.",
            ))

            # Exception 2: Missing record
            db.add(ReconciliationException(
                id=str(uuid.uuid4()),
                reconciliation_run_id=rec_run.id,
                exception_type=RecExceptionType.MISSING_BANK_RECORD,
                severity=RecExceptionSeverity.CRITICAL,
                status=RecExceptionStatus.INVESTIGATING,
                reference_key="CARD-REC-DROP-02",
                explanation="Payment marked SUCCEEDED in Switch, but simulated bank ledger has no corresponding authorization record.",
            ))
            db.commit()

        print("[SUCCESS] Database seeding completed successfully!")
    finally:
        db.close()
