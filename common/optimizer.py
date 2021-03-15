from typing import Any, List, Optional, Tuple

import numpy as np
from pydantic import BaseModel

from common.constant import (DEFAULT_DISCOUNT_APR,
                                     DEFAULT_RISK_AVERSION,
                                     DEFAULT_RISK_FREE_APR,
                                     DEFAULT_RISK_FREE_REPAY_PROBABILITY)
from common.loan import LoanInfo
from common.risk import BetaParams, RiskParams

# ===================== TO IMPOSE NDARRAY DATATYPE =====================
# see here for code: https://github.com/samuelcolvin/pydantic/issues/380


class _ArrayMeta(type):
    def __getitem__(self, t):
        return type("Array", (Array,), {"__dtype__": t})


class Array(np.ndarray, metaclass=_ArrayMeta):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate_type

    @classmethod
    def validate_type(cls, val):
        dtype = getattr(cls, "__dtype__", None)
        if isinstance(dtype, tuple):
            dtype, shape = dtype
        else:
            shape = tuple()

        result = np.array(val, dtype=dtype, copy=False, ndmin=len(shape))
        assert not shape or len(shape) == len(result.shape)  # ndmin guarantees this

        if any((shape[i] != -1 and shape[i] != result.shape[i]) for i in range(len(shape))):
            result = result.reshape(shape)
        return result


class LiveLoanInfo(LoanInfo):
    """ OUT OF DATE: extended info on live loans, will be needed by the optimizer """

    loan_id: str
    # interest: float #Note for Dju: what "interest" are we talking about here?
    risk_params: RiskParams  # @dju let's make this risk_params
    principal_outstand_corpus: float
    principal_outstand_supporters: float
    prds_remaining: int  # changed because time is measured in units of compounding periods
    prds_concluded: int  # need some way to know the tenor on the loan (as LiveLoanInfo does not inherit from LoanInfo)
    loan_schedule: Any  # pd.DataFrame (this is something we should fix at some point)
    # live_swap_info: Optional[LiveSwapInfo]


class OptimizerContext(BaseModel):
    risk_free_apr: float = DEFAULT_RISK_FREE_APR
    supporter_corpus_share: float
    loans_in_corpus: List[LiveLoanInfo]
    corpus_cash: float
    supporter_cash: float
    novation: bool = False
    discount_apr: float = DEFAULT_DISCOUNT_APR  # Need to include the discount rate
    pr_risk_free: BetaParams = DEFAULT_RISK_FREE_REPAY_PROBABILITY
    # corpus_info: Optional[CorpusInfo]
    # supporter_summary: Optional[
    # SupporterSummary
    # ]  # Made this optional just in case it breaks something, but otherwise should be produced by DB!


class OptimizerInputVectors(BaseModel):
    P: Array
    S: Array
    R: Array
    C: Array
    W: Array


class OptimizerInputLimits(BaseModel):
    trustLim: Tuple[float, float]
    wLim: Tuple[float, float]
    vLim: Tuple[float, float]
    rLim: Tuple[float, float]
    yLim_up: float
    cLim_lo: float
    cashCorpus: float
    cashSupporters: float
    loan_amount: float


class DemandFunction(BaseModel):
    M: int
    m: int
    k: int
    d: int
    n: int
    Xu: Array
    UZ: Array
    Q_qr: Array
    alpha: Array
    beta: Array
    phi: Array


class OptimizerInput(BaseModel):
    vectors: OptimizerInputVectors
    limits: OptimizerInputLimits
    corr_mtx: Array  # np.ndarray
    demand_function: Optional[DemandFunction]
    risk_aversion: float = DEFAULT_RISK_AVERSION


class OptimizerOutput(BaseModel):
    amount_asset_purchased: int
    pct_supp_portfolio_sold: float
    supp_corpus_loan_ratio: float
    desired_irr: float
    w_nov: Optional[float]
    r_nov: Optional[float]
    c_nov: Optional[float]
