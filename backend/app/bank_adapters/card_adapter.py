import uuid
import time
from typing import Optional, Any
from app.bank_adapters.base import BaseBankAdapter, BankExecutionResult


class CardBankAdapter(BaseBankAdapter):
    def authorize(self, payment: Any, scenario: Optional[str] = None) -> BankExecutionResult:
        auth_code = f"AUTH{int(time.time())}{uuid.uuid4().hex[:4].upper()}"

        if scenario == "BANK_UNAVAILABLE":
            return BankExecutionResult(
                is_success=False,
                status="FAILED",
                bank_reference=auth_code,
                error_code="CARD_NETWORK_UNAVAILABLE",
                error_message="Card network (Visa/Mastercard/RuPay simulator) unreachable",
                latency_ms=100,
            )

        if scenario == "INSUFFICIENT_FUNDS":
            return BankExecutionResult(
                is_success=False,
                status="DECLINED",
                bank_reference=auth_code,
                error_code="INSUFFICIENT_CREDIT_LIMIT",
                error_message="Simulated card balance / credit limit exceeded",
                latency_ms=75,
            )

        if scenario == "INVALID_DEMO_AUTH":
            return BankExecutionResult(
                is_success=False,
                status="DECLINED",
                bank_reference=auth_code,
                error_code="3DS_AUTH_FAILED",
                error_message="Customer 3-D Secure OTP verification failed",
                latency_ms=65,
            )

        if scenario == "TIMEOUT_AFTER_BANK_SUCCESS":
            return BankExecutionResult(
                is_success=True,
                status="SUCCESS",
                bank_reference=auth_code,
                latency_ms=1500,
                is_delayed=True,
                raw_response={"message": "Card authorization succeeded at bank, connection timed out"},
            )

        return BankExecutionResult(
            is_success=True,
            status="SUCCESS",
            bank_reference=auth_code,
            latency_ms=55,
            raw_response={"auth_code": auth_code, "action": "HOLD_AUTHORIZED"},
        )

    def capture(self, payment: Any, scenario: Optional[str] = None) -> BankExecutionResult:
        cap_ref = f"CAP{int(time.time())}{uuid.uuid4().hex[:4].upper()}"
        return BankExecutionResult(
            is_success=True,
            status="SUCCESS",
            bank_reference=cap_ref,
            latency_ms=30,
            raw_response={"capture_ref": cap_ref, "captured_amount_paise": payment.amount_paise},
        )

    def process_payment(self, payment: Any, scenario: Optional[str] = None) -> BankExecutionResult:
        # Step 1: Authorize
        auth_res = self.authorize(payment, scenario)
        if not auth_res.is_success or auth_res.is_delayed:
            return auth_res
        # Step 2: Auto capture if successful
        cap_res = self.capture(payment, scenario)
        cap_res.bank_reference = auth_res.bank_reference
        return cap_res

    def process_refund(self, refund: Any, original_payment: Any, scenario: Optional[str] = None) -> BankExecutionResult:
        ref_code = f"CARD-REF-{int(time.time())}{uuid.uuid4().hex[:4].upper()}"
        return BankExecutionResult(
            is_success=True,
            status="SUCCESS",
            bank_reference=ref_code,
            latency_ms=40,
            raw_response={"refund_reference": ref_code},
        )

    def query_status(self, bank_reference: str) -> BankExecutionResult:
        return BankExecutionResult(
            is_success=True,
            status="SUCCESS",
            bank_reference=bank_reference,
            latency_ms=25,
        )
