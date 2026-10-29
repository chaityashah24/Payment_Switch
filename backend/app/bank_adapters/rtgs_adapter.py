import uuid
import time
from typing import Optional, Any
from app.bank_adapters.base import BaseBankAdapter, BankExecutionResult

# Academic simulator threshold (e.g., minimum ₹2,000 = 200000 paise)
SIMULATOR_RTGS_MIN_PAISE = 200000


class RTGSBankAdapter(BaseBankAdapter):
    def process_payment(self, payment: Any, scenario: Optional[str] = None) -> BankExecutionResult:
        rtgs_utr = f"RTGS{int(time.time())}{uuid.uuid4().hex[:6].upper()}"

        # Threshold check
        if payment.amount_paise < SIMULATOR_RTGS_MIN_PAISE:
            return BankExecutionResult(
                is_success=False,
                status="DECLINED",
                bank_reference=rtgs_utr,
                error_code="RTGS_MIN_AMOUNT_NOT_MET",
                error_message=f"RTGS requires minimum transaction value of ₹{SIMULATOR_RTGS_MIN_PAISE // 100} in this simulation.",
                latency_ms=40,
            )

        if scenario == "BANK_UNAVAILABLE":
            return BankExecutionResult(
                is_success=False,
                status="FAILED",
                bank_reference=rtgs_utr,
                error_code="RTGS_GATEWAY_DOWN",
                error_message="RTGS Inter-Bank Settlement Core offline",
                latency_ms=90,
            )

        if scenario == "INSUFFICIENT_FUNDS":
            return BankExecutionResult(
                is_success=False,
                status="DECLINED",
                bank_reference=rtgs_utr,
                error_code="INSUFFICIENT_FUNDS",
                error_message="Account balance below required RTGS gross amount",
                latency_ms=60,
            )

        return BankExecutionResult(
            is_success=True,
            status="SUCCESS",
            bank_reference=rtgs_utr,
            latency_ms=50,
            raw_response={
                "utr": rtgs_utr,
                "gross_settled": True,
                "message": "Gross settlement completed immediately across central bank simulated clearing",
            },
        )

    def authorize(self, payment: Any, scenario: Optional[str] = None) -> BankExecutionResult:
        return self.process_payment(payment, scenario)

    def capture(self, payment: Any, scenario: Optional[str] = None) -> BankExecutionResult:
        return BankExecutionResult(
            is_success=True,
            status="SUCCESS",
            bank_reference=payment.bank_reference or f"RTGS-CAP-{uuid.uuid4().hex[:6].upper()}",
            latency_ms=20,
        )

    def process_refund(self, refund: Any, original_payment: Any, scenario: Optional[str] = None) -> BankExecutionResult:
        ref_utr = f"RTGS-REV-{uuid.uuid4().hex[:6].upper()}"
        return BankExecutionResult(
            is_success=True,
            status="SUCCESS",
            bank_reference=ref_utr,
            latency_ms=40,
        )

    def query_status(self, bank_reference: str) -> BankExecutionResult:
        return BankExecutionResult(
            is_success=True,
            status="SUCCESS",
            bank_reference=bank_reference,
            latency_ms=20,
        )
