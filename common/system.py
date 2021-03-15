from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel

from common.constant import DEFAULT_CENTRAL_SOURCE_REPUTATION
from common.loan import LoanRequest, Loans
from common.optimizer import OptimizerContext
from common.risk import BetaParams, ExternalRiskInfo, RiskInput
from common.user import AgentId, RoI, UserId, UserInfo

Entity = Dict[str, Any]
BalanceTable = Dict[str, float]
Edge = Tuple[AgentId, AgentId, int]
Network = Entity
RepaymentsList = List[Entity]
AgentInfoTable = Dict[AgentId, Any]
TRUSTOR = "trustor"
TRUSTEE = "trustee"
AssetType = Enum("AssetType", "CASH, PORTFOLIO")


# --------------------------- SYSTEM INFO -----------------------------
class SwarmAIRequestMessage(BaseModel):
    loan_request_info: LoanRequest
    risk_assessment_context: Optional[RiskInput]
    optimizer_context: Optional[OptimizerContext]


class Scenario(Loans):
    """
    A complete description of the system's state:
    - loans (requested, offered, live)
    - a collection of users
    - optionally with summarized info on who are lenders, borrowers, supporters
    """

    users: Dict[UserId, UserInfo] = {}
    lenders: Optional[List[UserId]]
    borrowers: Optional[List[UserId]]
    supporters: Optional[List[UserId]]


# --------------------------- STATE CHANGES -----------------------------
class TransactionPurpose(str, Enum):
    # lender/supporter to loan-escrow
    LEND = "lend"
    # loan-escrow to receivers
    DISBURSAL = "disbursal"
    # supporter to escrow before loan is accepted (not used atm)
    PLEDGE = "pledge"
    # lender/supporter change account balance themselves
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    # borrower repays (to escrow)
    INSTALLMENT = "installment"
    # borrower repayent is sent to corpus/supporter (from escrow)
    REPAYMENT = "repayment"


class Transaction(BaseModel):
    sender: UserId
    receiver: UserId
    amount: float
    purpose: Optional[TransactionPurpose]


class PortfolioUpdate(BaseModel):
    userId: UserId
    balanceDelta: float = 0
    shareDelta: float = 0
    newRoI: RoI = RoI()
    # alias: Optional[str]


class BalanceChange(BaseModel):
    user_id: UserId
    new_balance: float
    old_balance: Optional[float]


class AccountsUpdate(BaseModel):
    updates: List[PortfolioUpdate] = []
    transactions: Optional[List[Transaction]]
    escrow_deltas: Dict[str, float] = {}


class SystemUpdate(BaseModel):
    loans: Loans
    accounts: AccountsUpdate


class RiskRequestMessage(BaseModel):
    borrower_id: AgentId
    loan_size: int
    network_dict: Dict
    # every agent maintains a lookup of other agent
    recommendation_risks: Dict[AgentId, AgentInfoTable]
    repayments: Dict[AgentId, RepaymentsList]
    potential_lenders: List[AgentId]
    portfolio_sizes: AgentInfoTable
    central_source_info: ExternalRiskInfo
    central_source_reputation: BetaParams = DEFAULT_CENTRAL_SOURCE_REPUTATION
    w: int = 0


class PaymentSplit(BaseModel):
    principal: float = 0
    interest: float = 0


class RepaymentBreakdown(BaseModel):
    influx: float
    to_corpus: PaymentSplit
    to_supporter: float
    to_escrow: Optional[float]
