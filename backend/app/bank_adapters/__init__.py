from app.models.payment import PaymentMethod
from app.bank_adapters.base import BaseBankAdapter, BankExecutionResult
from app.bank_adapters.upi_adapter import UPIBankAdapter
from app.bank_adapters.card_adapter import CardBankAdapter
from app.bank_adapters.neft_adapter import NEFTBankAdapter
from app.bank_adapters.rtgs_adapter import RTGSBankAdapter

ADAPTERS = {
    PaymentMethod.UPI: UPIBankAdapter(),
    PaymentMethod.CARD: CardBankAdapter(),
    PaymentMethod.NEFT: NEFTBankAdapter(),
    PaymentMethod.RTGS: RTGSBankAdapter(),
}


def get_bank_adapter(method: PaymentMethod) -> BaseBankAdapter:
    return ADAPTERS[method]
