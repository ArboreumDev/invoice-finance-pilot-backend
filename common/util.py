from pydantic import BaseModel

from common.constant import DEFAULT_PRECISION_MONEY
from common.exceptions import InternalError
from utils.helpers import money_matches


class PaidRemain(BaseModel):
    paid: float = 0
    remain: float = 0
    # TODO add add & equals operator

    def __eq__(self, other):
        return money_matches(self.paid, other.paid) and money_matches(self.remain, other.remain)

    def __add__(self, other):
        return PaidRemain(paid=self.paid + other.paid, remain=self.remain + other.remain)

    def total(self):
        """ return sum of paid & remain """
        return self.paid + self.remain


class APR(BaseModel):
    corpus: float = 0
    supporter: float = 0


class APRInfo(BaseModel):
    apr: float = 0
    interest: PaidRemain = PaidRemain()
    principal: PaidRemain = PaidRemain()

    def __eq__(self, other):
        return self.apr == other.apr and self.interest == other.interest and self.principal == other.principal

    def __add__(self, other):
        """
        return a new APRInfo as a sum of two given APRs, apr weighted by their respective outstanding amounts
        for apr: amounts smaller than our MONEY_PRECISION are regarded as zero
        """
        w_a = self.principal.remain if self.principal.remain > 10 ** -(DEFAULT_PRECISION_MONEY + 1) else 0
        w_b = other.principal.remain if other.principal.remain > 10 ** -(DEFAULT_PRECISION_MONEY + 1) else 0
        if w_a < 0 or w_b < 0:
            raise InternalError("weights must be positive")

        return APRInfo(
            apr=(self.apr * w_a + other.apr * w_b) / (w_a + w_b) if (w_a or w_b) else 0,
            principal=self.principal + other.principal,
            interest=self.interest + other.interest,
        )
