from typing import Optional, Any, Dict
from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.correlation import get_correlation_id


class SwitchException(Exception):
    def __init__(self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, details: Optional[Any] = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class AuthenticationError(SwitchException):
    def __init__(self, message: str = "Invalid credentials", details: Optional[Any] = None):
        super().__init__(code="AUTHENTICATION_FAILED", message=message, status_code=status.HTTP_401_UNAUTHORIZED, details=details)


class PermissionDeniedError(SwitchException):
    def __init__(self, message: str = "You do not have permission to access this resource", details: Optional[Any] = None):
        super().__init__(code="FORBIDDEN", message=message, status_code=status.HTTP_403_FORBIDDEN, details=details)


class NotFoundError(SwitchException):
    def __init__(self, resource: str, identifier: str):
        super().__init__(code="NOT_FOUND", message=f"{resource} '{identifier}' not found", status_code=status.HTTP_404_NOT_FOUND)


class ConflictError(SwitchException):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(code="CONFLICT", message=message, status_code=status.HTTP_409_CONFLICT, details=details)


class InsufficientFundsError(SwitchException):
    def __init__(self, message: str = "Insufficient funds in customer simulated account"):
        super().__init__(code="INSUFFICIENT_FUNDS", message=message, status_code=status.HTTP_400_BAD_REQUEST)


class InvalidStateTransitionError(SwitchException):
    def __init__(self, from_state: str, to_state: str):
        super().__init__(
            code="INVALID_STATE_TRANSITION",
            message=f"Illegal transition from '{from_state}' to '{to_state}'",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class LedgerImbalanceError(SwitchException):
    def __init__(self, total_debit: int, total_credit: int):
        super().__init__(
            code="LEDGER_IMBALANCE",
            message=f"Journal entry debits ({total_debit}) do not balance credits ({total_credit})",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def switch_exception_handler(request: Request, exc: SwitchException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "correlation_id": get_correlation_id(),
                "details": exc.details,
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred while processing the request",
                "correlation_id": get_correlation_id(),
                "details": str(exc) if "development" in request.app.state.env else None,
            }
        },
    )
