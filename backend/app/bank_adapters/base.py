from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel


class BankExecutionResult(BaseModel):
    is_success: bool
    status: str  # SUCCESS, DECLINED, PENDING, FAILED
    bank_reference: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    latency_ms: int = 50
    raw_response: Dict[str, Any] = {}
    is_delayed: bool = False


class BaseBankAdapter(ABC):
    @abstractmethod
    def process_payment(self, payment: Any, scenario: Optional[str] = None) -> BankExecutionResult:
        """Process a direct payment transaction."""
        pass

    @abstractmethod
    def authorize(self, payment: Any, scenario: Optional[str] = None) -> BankExecutionResult:
        """Authorize funds (holds balance)."""
        pass

    @abstractmethod
    def capture(self, payment: Any, scenario: Optional[str] = None) -> BankExecutionResult:
        """Capture pre-authorized funds."""
        pass

    @abstractmethod
    def process_refund(self, refund: Any, original_payment: Any, scenario: Optional[str] = None) -> BankExecutionResult:
        """Process refund through simulated bank."""
        pass

    @abstractmethod
    def query_status(self, bank_reference: str) -> BankExecutionResult:
        """Query independent bank status."""
        pass
