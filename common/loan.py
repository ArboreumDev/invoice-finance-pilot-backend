import datetime as dt
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel

from common.constant import (DEFAULT_ANNUAL_COMPOUND_PERIODS,
                                     DEFAULT_PENALTY_APR,
                                     DEFAULT_SUPPORTER_LAG)
from common.risk import BetaParams
from common.user import BorrowerInfo, SupporterInfo
from common.util import APR, PaidRemain

RepaymentDate = dt.datetime
Repayment = Tuple[RepaymentDate, float]


class BaseLoan(BaseModel):
    """ basic info to identify loan """

    request_id: str


class RequestedTerms(BaseLoan):
    """ terms of the loan as requested by borrower, not subject to change """

    borrower_info: BorrowerInfo
    request_id: str
    tenor: float
    amount: float  # TODO change to principal to be more precise
    supporters: List[SupporterInfo]
    # filled by us for the borrower
    borrower_collateral: float
    num_annual_cmpnd_prds: int = DEFAULT_ANNUAL_COMPOUND_PERIODS


class OfferedTerms(RequestedTerms):
    """ filled by ai, when a loan is offered, not subject to change """

    corpus_share: float
    corpus_apr: float
    supporter_share: float
    supporter_apr: float
    borrower_apr: float
    supporter_lag: int = DEFAULT_SUPPORTER_LAG  # lag period for holding supporter cash, anti-collusion
    penalty_apr: float = DEFAULT_PENALTY_APR
    # swap_info: Optional[SwapInfo]


class LoanRequest(BaseLoan):
    """ Info needed to get an offer: supporters & risk info & system parameters """

    # NOTE: for now it is only the terms from the borrower, but as soon as we use a more complicated
    # risk model, we need more parameters
    terms: RequestedTerms
    risk_params: Optional[BetaParams]


class LoanState(BaseLoan):
    """ params that change over the course of the loan-lifecycle """

    borrower_collateral: float
    repayments: Optional[List[float]] = []
    supporter_cash_encumbered: float = 0
    supporter_portfolio_encumbered: float = 0
    escrow: float = 0


class BorrowerView(BaseModel):
    total_payments: PaidRemain
    corpus_principal: PaidRemain
    supporter_principal: PaidRemain
    corpus_interest: PaidRemain
    supporter_interest: PaidRemain
    borrower_collateral: PaidRemain


class SupporterView(BaseModel):
    total_receipts: PaidRemain
    supporter_principal: PaidRemain
    supporter_interest: PaidRemain
    receipts_in_escrow: PaidRemain
    # "receipts_sent2corp",
    receipts_rtrn_from_brw: PaidRemain
    cash_unencumbered: PaidRemain
    # "cash_sent2corp",
    cash_rtrn_from_brw: PaidRemain
    ptfl_unencumbered: PaidRemain
    ptfl_rtrn_from_brw: PaidRemain
    principal_released: PaidRemain
    interest_released: PaidRemain
    total_released: PaidRemain


class CorpusView(BaseModel):
    total_receipts: PaidRemain
    principal: PaidRemain
    interest: PaidRemain


class LoanScheduleSummary(BaseLoan):
    """ Basic info and breakdown on what needs and has to be payed to whom """

    borrower_view: BorrowerView
    next_borrower_payment: float
    supporter_view: SupporterView
    corpus_view: CorpusView
    apr: APR = APR()
    full_single_repay: Optional[float]


class LoanInfo(BaseLoan):
    terms: OfferedTerms
    state: LoanState
    schedule: LoanScheduleSummary


# Alias to make things more readable
LoanOffer = LoanInfo


class Loans(BaseModel):
    """
    Dicts of all loans in all 3 different stages:
        - requested
        - offered (but not accepted)
        - accepted and live
    Note: One set of loans can be updated with another, so this class can both describe
    the system and an update to it
    """

    loan_requests: Dict[str, LoanRequest] = {}
    loan_offers: Dict[str, LoanInfo] = {}
    loans: Dict[str, LoanInfo] = {}  # refactor: live_loans would be more helpful when parsing written code
