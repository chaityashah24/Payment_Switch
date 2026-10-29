import re
import uuid
import time
from typing import Optional, Any
from app.bank_adapters.base import BaseBankAdapter, BankExecutionResult

UPI_VPA_REGEX = re.compile(r"^[a-zA-Z0-9.\-_]{2,}@[a-zA-Z]{2,}$")


class UPIBankAdapter(BaseBankAdapter):
    def validate_vpa(self, vpa: str) -> bool:
        return bool(UPI_VPA_REGEX.match(vpa.strip()))

    def process_payment(self, payment: Any, scenario: Optional[str] = None) -> BankExecutionResult:
        bank_ref = f"UPI{int(time.time())}{uuid.uuid4().hex[:6].upper()}"

        # Evaluate scenario
        if scenario == "BANK_UNAVAILABLE":
            return BankExecutionResult(
                is_success=False,
                status="FAILED",
                bank_reference=bank_ref,
                error_code="BANK_UNAVAILABLE",
                error_message="Simulated NPCI / Bank Switch gateway unreachable (HTTP 503)",
                latency_ms=120,
            )

        if scenario == "INSUFFICIENT_FUNDS":
            return BankExecutionResult(
                is_success=False,
                status="DECLINED",
                bank_reference=bank_ref,
                error_code="INSUFFICIENT_FUNDS",
                error_message="Customer bank account has insufficient balance for transaction",
                latency_ms=80,
            )

        if scenario == "INVALID_DEMO_AUTH":
            return BankExecutionResult(
                is_success=False,
                status="DECLINED",
                bank_reference=bank_ref,
                error_code="INVALID_UPI_PIN",
                error_message="Customer entered an incorrect 4-digit UPI MPIN in simulation",
                latency_ms=60,
            )

        if scenario == "TIMEOUT_BEFORE_PROCESSING":
            return BankExecutionResult(
                is_success=False,
                status="PENDING",
                bank_reference=bank_ref,
                error_code="REQUEST_TIMEOUT",
                error_message="Connection timed out before reaching bank core",
                latency_ms=1500,
                is_delayed=True,
            )

        if scenario == "TIMEOUT_AFTER_BANK_SUCCESS":
            # Bank actually processed successfully, but the network timed out on the return trip to the switch!
            return BankExecutionResult(
                is_success=True,
                status="SUCCESS",
                bank_reference=bank_ref,
                latency_ms=1500,
                is_delayed=True,
                raw_response={"message": "Processed at bank, acknowledgement lost in transit"},
            )

        if scenario == "SLOW_RESPONSE":
            return BankExecutionResult(
                is_success=True,
                status="SUCCESS",
                bank_reference=bank_ref,
                latency_ms=800,
                is_delayed=True,
            )

        # Default standard execution
        return BankExecutionResult(
            is_success=True,
            status="SUCCESS",
            bank_reference=bank_ref,
            latency_ms=45,
            raw_response={"vpa": payment.instrument_ref, "message": "UPI payment approved by simulated issuer"},
        )

    def authorize(self, payment: Any, scenario: Optional[str] = None) -> BankExecutionResult:
        return self.process_payment(payment, scenario)

    def capture(self, payment: Any, scenario: Optional[str] = None) -> BankExecutionResult:
        return BankExecutionResult(
            is_success=True,
            status="SUCCESS",
            bank_reference=payment.bank_reference or f"UPI-CAP-{uuid.uuid4().hex[:6].upper()}",
            latency_ms=20,
        )

    def process_refund(self, refund: Any, original_payment: Any, scenario: Optional[str] = None) -> BankExecutionResult:
        bank_ref = f"UPI-REF-{int(time.time())}{uuid.uuid4().hex[:4].upper()}"
        return BankExecutionResult(
            is_success=True,
            status="SUCCESS",
            bank_reference=bank_ref,
            latency_ms=50,
            raw_response={"refund_amount_paise": refund.amount_paise},
        )

    def query_status(self, bank_reference: str) -> BankExecutionResult:
        return BankExecutionResult(
            is_success=True,
            status="SUCCESS",
            bank_reference=bank_reference,
            latency_ms=30,
        )
