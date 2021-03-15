import copy
from typing import Any, Dict, List

import numpy as np

from common.constant import DEFAULT_PRECISION_MONEY
from common.exceptions import InternalError
from common.loan import LoanInfo, LoanState, OfferedTerms
from common.system import (PaymentSplit, PortfolioUpdate,
                                   RepaymentBreakdown)
from common.user import SupporterInfo
from common.util import APR, APRInfo, PaidRemain
from loan.loan import Loan
from utils.helpers import proportion

# import functools


LoanSchedule = Any
# given a loan class how to abstract logic relevant for different scenarios


def loanInfo_to_LoanInstance(loan: LoanInfo):
    return loanState_to_LoanInstance(loan.terms, loan.state)


def loanState_to_LoanInstance(terms: OfferedTerms, state: LoanState):
    """ helper function to account for the abbreviated variable names inside the loan-class """
    return Loan(
        corp_APR=terms.corpus_apr,
        sprt_APR=terms.supporter_apr,
        loan_amt=terms.amount,
        loan_tnr=terms.tenor,
        sprt_shr=terms.supporter_share,
        sprt_cash_encumbr=state.supporter_cash_encumbered,
        sprt_ptfl_encumbr=state.supporter_portfolio_encumbered,
        brw_collateral=state.borrower_collateral,
        repayments=state.repayments,
        sprt_lag=terms.supporter_lag,
        penalty_APR=terms.penalty_apr,
        id=terms.request_id,
    )


def get_full_repayment(loan: Loan):
    sum, next = loan.summarize_schedule()
    total_remain = sum.loc["total_payments", "remain"]
    return total_remain


def loanState_to_schedule_summary(terms: OfferedTerms, state: LoanState):
    instance = loanState_to_LoanInstance(terms, state)
    return instance.summary()


def get_apr(terms: OfferedTerms, state: LoanState, instance: Loan):
    corpus_irr = instance.schedule_DF.loc["corp_IRR", len(state.repayments)]
    supporter_irr = instance.schedule_DF.loc["sprt_IRR", len(state.repayments)]
    supporter_apr = 0
    if supporter_irr == supporter_irr:
        # only do if not nan
        supporter_apr = Loan.calc_APR_NPV(terms.amount, terms.tenor, supporter_irr)[0]
    return APR(corpus=Loan.calc_APR_NPV(terms.amount, terms.tenor, corpus_irr)[0], supporter=supporter_apr)


def mutate_loan(loan: Dict, key: str, value: Any):
    """
    takes the description of a loan object (LoanInfo) and a field that should be changed
    returns a Loan-class that only differs in the specified key
    """
    l2 = copy.deepcopy(loan)
    l2[key] = value
    return Loan(**l2)


def proportion_of_PaidRemain(part: float, total: float, amount: PaidRemain):
    """ computes the part/total of amount.remain & amount.paid """
    # print('in prop', part, total, amount.remain)
    return PaidRemain(paid=proportion(part, total, amount.paid), remain=proportion(part, total, amount.remain))


def proportion_of_APR(part: float, total: float, a: APRInfo):
    return APRInfo(
        apr=a.apr,
        principal=proportion_of_PaidRemain(part, total, a.principal),
        interest=proportion_of_PaidRemain(part, total, a.interest),
    )


def get_payment_breakdown(loan_info: LoanInfo):
    loan_instance: Loan = loanInfo_to_LoanInstance(loan_info)
    # create new schedule inclduing the new payment to be used to calculate how much to disburse to whom
    schedule = loan_instance.calc_schedule().schedule_DF
    # print(schedule)
    # the payment schedule keeps track of what has been paid to the corpus/supporter and each down into
    # payments towards principal and interest, for each repayment that happened, plus a virtual first payment.
    # Thus the total to be repayed is the sum of principal + interest
    # in the column that equals the number of the current  repayment (idx)
    idx = len(loan_info.state.repayments)
    repayment = loan_info.state.repayments[-1]
    to_corpus = PaymentSplit(
        principal=np.round(schedule.loc["corp_prcp_paid_actual", idx], DEFAULT_PRECISION_MONEY + 1),
        interest=np.round(schedule.loc["corp_intr_paid_actual", idx], DEFAULT_PRECISION_MONEY + 1),
    )
    to_supporter = np.round(schedule.loc["sprt_2pay_now", idx], DEFAULT_PRECISION_MONEY + 1)

    breakdown = RepaymentBreakdown(
        influx=repayment,
        to_corpus=to_corpus,
        to_supporter=to_supporter,
    )
    assert_payment_breakdown_consistency(repayment, breakdown, loan_info.state.escrow)
    return breakdown


def total(p: PaymentSplit):
    return p.interest + p.principal


def get_total_lender_updates(updates: List[PortfolioUpdate], supporters: List[SupporterInfo]):
    total_disbursed_to_lenders = 0
    for u in updates:
        supporter_ids = [s.supporter_id for s in supporters]
        if u.balanceDelta > 0 and u.userId not in supporter_ids:
            total_disbursed_to_lenders += u.balanceDelta
    return total_disbursed_to_lenders


def assert_payment_breakdown_consistency(amount: float, payments: RepaymentBreakdown, escrow: float):
    """
    - verify escrow can outgoing payments
    - verify that amount of money in system stays the same
    """
    if total(payments.to_corpus) + payments.to_supporter > escrow + amount:
        raise InternalError("Invalid breakdown! Escrow can not be negative")
    return True
