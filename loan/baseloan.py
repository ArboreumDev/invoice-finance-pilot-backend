from abc import ABC, abstractmethod
from typing import Any, List

from common.loan import LoanScheduleSummary
from common.system import RepaymentBreakdown


class BaseLoan(ABC):
    def __init__(self, loan_amount: float, tenor: int, repayments: List[Any], id: str):
        self.repayments = repayments
        self.id = id
        self.loan_amount = loan_amount
        self.tenor = tenor

    @property
    @abstractmethod
    def fully_repaid(self) -> bool:
        ...

    @property
    @abstractmethod
    def status(self) -> str:
        """
        loan state beyond repaid <> not repaid, eg. to be used return info on defaults.
        Recommended: "live", "repaid", "overdue", "defaulted"
        """
        ...

    @property
    @abstractmethod
    def escrow(self) -> bool:
        """ how much is currently being held in escrow, if escrow is not used, return zero """
        ...

    # @abstractmethod
    # def update_schedule(self, repayments: List[Repayment]) -> LoanScheduleSummary:
    #     """ update schedule and internal state to account for given repayments """
    #     ...

    @abstractmethod
    def summary(self) -> LoanScheduleSummary:
        """ summarize essential information on the loan from schedule dataFrame """
        ...

    @abstractmethod
    def get_payment_breakdown(self) -> RepaymentBreakdown:
        """
        given the latest repayments, return how much is to be released to supporter, corpus and
        how much goes to_escrow (which can be negative in which case escrow must have been nonzero before)
        """
        ...
