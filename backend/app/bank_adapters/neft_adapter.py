import uuid
import time
from typing import Optional, Any
from app.bank_adapters.base import BaseBankAdapter, BankExecutionResult


class NEFTBankAdapter(BaseBankAdapter):
    def process_payment(self, payment: Any, scenario: Optional[str] = None) -> BankExecutionResult:
        neft_batch_ref = f"NEFT-BATCH-{int(time.time() // 3600)}-{uuid.uuid4().hex[:6].upper()}"

        if scenario == "BANK_UNAVAILABLE":
            return BankExecutionResult(
                is_success=False,
                status="FAILED",
                bank_reference=neft_batch_ref,
                error_code="RBI_NEFT_CLEARING_UNAVAILABLE",
                error_message="National Electronic Funds Transfer batch clearing cycle unavailable",
                latency_ms=100,
            )

        if scenario == "INSUFFICIENT_FUNDS":
            return BankExecutionResult(
                is_success=False,
                status="DECLINED",
                bank_reference=neft_batch_ref,
                error_code="INSUFFICIENT_FUNDS",
                error_message="Simulated bank account does not have sufficient balance for NEFT transfer",
                latency_ms=80,
            )

        # NEFT transactions enter QUEUED / BATCH_PENDING by design
        return BankExecutionResult(
            is_success=True,
            status="QUEUED",
            bank_reference=neft_batch_ref,
            latency_ms=50,
            is_delayed=True,
            raw_response={
                "batch_reference": neft_batch_ref,
                "message": "Payment queued for next hourly simulated NEFT clearing batch",
            },
        )

    def authorize(self, payment: Any, scenario: Optional[str] = None) -> BankExecutionResult:
        return self.process_payment(payment, scenario)

    def capture(self, payment: Any, scenario: Optional[str] = None) -> BankExecutionResult:
        return BankExecutionResult(
            is_success=True,
            status="SUCCESS",
            bank_reference=payment.bank_reference or f"NEFT-CAP-{uuid.uuid4().hex[:6].upper()}",
            latency_ms=20,
        )

    def process_refund(self, refund: Any, original_payment: Any, scenario: Optional[str] = None) -> BankExecutionResult:
        ref_code = f"NEFT-REV-{uuid.uuid4().hex[:6].upper()}"
        return BankExecutionResult(
            is_success=True,
            status="SUCCESS",
            bank_reference=ref_code,
            latency_ms=45,
        )

    def query_status(self, bank_reference: str) -> BankExecutionResult:
        return BankExecutionResult(
            is_success=True,
            status="SUCCESS",
            bank_reference=bank_reference,
            latency_ms=30,
        )
