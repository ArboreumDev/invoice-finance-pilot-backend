from typing import Any, Dict, Optional

from pydantic import BaseModel

from common.constant import DEFAULT_SUPPORTER_APR_DELTA
from common.risk import RiskParams
from common.util import APRInfo

AgentId = int  # REFACTOR: should be str
UserId = Any


# --------------------------- USER INFO -----------------------------
class BaseUser(BaseModel):
    id: UserId
    balance: float


class CorpusMember(BaseUser):
    corpus_share: float


class SupporterDemographicInfo(BaseModel):
    """ info that will be helpful to gauge risk, but for now is optional """

    education_years: Optional[int]
    income: Optional[int]
    credit_score: Optional[float]


# Demographics of borrowers
class BorrowerDemographicInfo(BaseModel):
    """ info that we need to gauge risk, sonme of it optional """

    education_years: Optional[int]
    income: int
    credit_score: float


class LoanSummary(BaseModel):
    sum: APRInfo() = APRInfo()
    loans: Dict[str, APRInfo] = {}


# return of investment
class RoI(BaseModel):
    total_apr: APRInfo = APRInfo()
    apr_on_pledges: LoanSummary = LoanSummary()
    apr_on_loans: LoanSummary = LoanSummary()

    def __eq__(self, other):
        return (
            self.total_apr == other.total_apr
            and self.apr_on_loans.sum == other.apr_on_loans.sum
            and self.apr_on_pledges.sum == other.apr_on_pledges.sum
        )

    def update(self):
        self.apr_on_loans.sum = APRInfo()
        for loan_apr in self.apr_on_loans.loans.values():
            self.apr_on_loans.sum += loan_apr

        self.apr_on_pledges.sum = APRInfo()
        for loan_apr in self.apr_on_pledges.loans.values():
            self.apr_on_pledges.sum += loan_apr

        self.total_apr = self.apr_on_loans.sum + self.apr_on_pledges.sum


class UserInfo(BaseUser):
    """ basic info we actually store on our users """

    name: str
    email: str
    user_type: str
    demographic_info: SupporterDemographicInfo
    roi: RoI = RoI()
    corpus_share: float = 0
    encumbered_cash: float = 0
    encumbered_portfolio: float = 0


# Static attributes of borrowers
class BorrowerInfo(BaseModel):
    """ info on borrower used inside a loan-object """

    borrower_id: str
    demographic_info: BorrowerDemographicInfo


# Static and Dynamic attributes of supporters +portfolioo(ths should ideally be separated -- see below)
class SupporterInfo(BaseModel):
    supporter_id: str
    recommendation_risk: RiskParams
    demographic_info: Optional[SupporterDemographicInfo]  # to assess recommendation risk
    trust_amount: float
    # cash_in_trust_channel: float  # amount of trust that is cash
    # ptfl_in_trust_channel: float  # amount of trust that is portfolio
    # min_pct_direct_lend: float = DEFAULT_SUPPORTER_MIN_DIRECT_LEND  # minimum % supporter wants to directly lend
    apr_delta: float = DEFAULT_SUPPORTER_APR_DELTA  # difference between supporter and corpus APR
    # portfolio: Portfolio  # supporter portfolio will have participation exclusions instead of loans in portfolio)


class JWTUser(BaseModel):
    username: str
    password: str
    role: str = ""
