from typing import List

from common.constant import DEFAULT_PRECISION_MONEY
from common.loan import BorrowerView, LoanInfo, LoanScheduleSummary
from common.system import Scenario
from common.user import RoI, UserInfo
from common.util import PaidRemain
from loan.baseloan import BaseLoan
from loan.loan_helpers import loanInfo_to_LoanInstance
from utils.helpers import money_matches

FRACTIONAL_AMOUNT = 10 ** -(DEFAULT_PRECISION_MONEY - 1)
# ============================= REPAYMENT HELPERS =====================================


def add_x_regular_repayments_to_loan(loan: BaseLoan, x: int):
    i = 0
    while i < x:
        next_payment = loan.summary().next_borrower_payment
        loan.calc_schedule(loan.repayments + [next_payment])
        i += 1
    return loan


def complete_loan_with_regular_payments(loan: BaseLoan):
    n_missing_payments = loan.tenor - len(loan.repayments)
    return add_x_regular_repayments_to_loan(loan, n_missing_payments)


# =============================== VERIFICATION HELPERS Loan-class level ==================================
# helpers to check whether a loan schedule has adjusted as expected given a repayment


def assert_timely_repayment_registered_correctly(before: BaseLoan, after: BaseLoan, timely_repayment: float):
    """
    a regular payment is made: verifies sure that no money is being lost,
    no penalty has been applied and the payment is registered
    """
    before_summary = before.summary()
    after_summary = after.summary()

    # ballpark checks: verify less remain, more paid, less to repay at once
    assert before_summary.borrower_view.total_payments.remain > after_summary.borrower_view.total_payments.remain
    assert before_summary.borrower_view.total_payments.paid < after_summary.borrower_view.total_payments.paid
    assert before_summary.full_single_repay > after_summary.full_single_repay, "full single repay didnt decrease"

    # correct amount registered as paid
    assert after.repayments[-1] == timely_repayment

    # correct amount withdrawn from outstanding balance
    assert money_matches(
        after_summary.borrower_view.total_payments.remain + timely_repayment,
        before_summary.borrower_view.total_payments.remain,
    )

    # total size of loan is unchanged
    assert_total_ever_owed_is_unchanged(before_summary, after_summary)


def assert_underpayment_registered_correctly(before: BaseLoan, after: BaseLoan, underpayment: float):
    """ a penalty should have been applied, because the repayment was too little """
    before_summary = before.summary()
    after_summary = after.summary()

    # verify the payment has registered
    assert money_matches(
        before_summary.borrower_view.total_payments.paid, after_summary.borrower_view.total_payments.paid - underpayment
    )

    # verify that what remains is slighly more than what the repayment paid back, because a penalty was applied
    assert (
        before_summary.borrower_view.total_payments.remain
        < after_summary.borrower_view.total_payments.remain + underpayment
    ), f"""{before_summary.borrower_view.total_payments.remain} vs
        {after_summary.borrower_view.total_payments.remain + underpayment}"""
    # this should be true for all items
    assert_total_ever_owed_has_increased(before_summary, after_summary)

    # the total amount of money in the system is consistent between two states
    total_value_in_loan_is_consistent(before, after, underpayment)


# TODO how to check the payment breakdown


def total_value_in_loan_is_consistent(before: BaseLoan, after: BaseLoan, repaid_amount: float):
    """
    verify that the value of money in the loan increases correctly and that the internal repayments record
    matches the schedule & escrow
    """
    before_summary, after_summary = before.summary(), after.summary()

    # verify borrower view is consistent
    total_money_before = before_summary.borrower_view.total_payments.paid
    total_money_after = after_summary.borrower_view.total_payments.paid
    assert total_money_before + repaid_amount == total_money_after

    def received_by_corpus(loan: BaseLoan):
        raise NotImplementedError

    def received_by_supporter(loan: BaseLoan):
        raise NotImplementedError

    # verify that whatever has been paid to supporter & corpus + escrow is consistent
    # given_out_before = received_by_corpus(before) + received_by_supporter(before)
    given_out_before = (
        before_summary.corpus_view.total_receipts.paid + before_summary.supporter_view.total_released.paid
    )

    # given_out_after = received_by_corpus(after) + received_by_supporter(after)
    given_out_after = after_summary.corpus_view.total_receipts.paid + after_summary.supporter_view.total_released.paid

    assert money_matches(given_out_after + after.escrow, given_out_before + before.escrow + repaid_amount)

    # before
    # supporter_received == receitps in escrow paid
    # supporter_received + corpus_received + escrow + repaid_amount
    # ==
    # supporter_received + corpus_received + escrow
    # # after

    # total_money_after = after_summary.supporter_view['receipts_in_escrow']['paid']\
    #                     + after_summary.supporter_view['receipts_in_escrow']['remain']\
    #                     + after_summary.corpus_view['total_receipts']['paid']

    assert money_matches(amount1=total_money_before + repaid_amount, amount2=total_money_after)

    # verify that repayments have been updated correctly
    assert money_matches(sum(before.repayments) + repaid_amount, sum(after.repayments))

    # verify that schedules align with repayment array
    assert money_matches(sum(after.repayments), total_money_after)


# before last repayment
# - next_repay should be the same as full_single_repay


def loan_is_repaid(loan: BaseLoan):
    summary = loan.summary()
    return (
        schedule_has_zero_outstanding_debt(summary)
        and loan.fully_repaid
        and nothing_in_escrow(loan)
        and assert_view_is_consistent(summary.borrower_view)
        and loan.status != "live"
        and loan.status == "settled"
        and money_matches(sum(loan.repayments), summary.borrower_view.total_payments.paid)
    )


def loan_is_defaulted(loan: BaseLoan):
    summary = loan.summary()
    return (
        not schedule_has_zero_outstanding_debt(summary)
        and summary.next_borrower_payment > 0
        and summary.full_single_repay > 0  # TODO
        and not loan.fully_repaid
        and nothing_in_escrow(loan)
        and loan.status != "live"
        and loan.status == "defaulted"
        and assert_view_is_consistent(summary.borrower_view)
    )


def nothing_in_escrow(loan: BaseLoan):
    # return 0 <= loan.escrow <= FRACTIONAL_AMOUNT and loan.get_payment_breakdown().to_escrow <= FRACTIONAL_AMOUNT
    return 0 <= loan.escrow <= FRACTIONAL_AMOUNT


# partial default:
# - remainder should be nonzero
# - next payment nonzero
# - full_single_repay nonzero
# - withheld should be zero
# - assert that total paid to corpus & supporter matches total repayments


# full default:
# - remainder should be nonzero
# - next payment nonzero
# - full_single_repay nonzero
# - withheld should be zero
# - assert that total paid to corpus & supporter matches total repayments


# # LOAN DEFAULT


# # ALL LOANS COMPLETE


# =============================== VERIFICATION HELPERS Schedule-level ==================================


def schedule_has_zero_outstanding_debt(schedule: LoanScheduleSummary, precision: int = DEFAULT_PRECISION_MONEY):
    view = schedule.borrower_view
    nothing_left = (
        view.total_payments.remain <= FRACTIONAL_AMOUNT
        and view.corpus_principal.remain <= FRACTIONAL_AMOUNT
        and view.corpus_interest.remain <= FRACTIONAL_AMOUNT
        and view.supporter_interest.remain <= FRACTIONAL_AMOUNT
        and view.supporter_principal.remain <= FRACTIONAL_AMOUNT
        and schedule.next_borrower_payment <= FRACTIONAL_AMOUNT
        and schedule.full_single_repay <= FRACTIONAL_AMOUNT
    )

    # NOTE: if other perspectives are used, those should be checked to be consistent with the borrower view
    # consistent_perspectives = assert_all_perspectives_are_internally_consistent(schedule)

    return nothing_left


def assert_view_is_consistent(view: BorrowerView):
    total_paid = (
        view.corpus_interest.paid
        + view.corpus_principal.paid
        + view.supporter_principal.paid
        + view.supporter_interest.paid
    )
    total_remain = (
        view.corpus_interest.remain
        + view.corpus_principal.remain
        + view.supporter_principal.remain
        + view.supporter_interest.remain
    )
    assert money_matches(view.total_payments.paid, total_paid), "paid columns do not check out"
    assert money_matches(view.total_payments.remain, total_remain), "remain columns do not check out"
    return True


def assert_total_ever_owed_is_unchanged(before: LoanScheduleSummary, after: LoanScheduleSummary):
    """ verify that sum of paid & remain has stayed the same for summary and breakdown """
    assert money_matches(before.borrower_view.total_payments.total(), after.borrower_view.total_payments.total())
    assert money_matches(before.borrower_view.corpus_principal.total(), after.borrower_view.corpus_principal.total())
    assert money_matches(before.borrower_view.corpus_interest.total(), after.borrower_view.corpus_interest.total(), 1)
    assert money_matches(
        before.borrower_view.supporter_interest.total(), after.borrower_view.supporter_interest.total(), 1
    )
    assert money_matches(
        before.borrower_view.supporter_principal.total(), after.borrower_view.supporter_principal.total(), 1
    )

    # assert before.borrower_view.total_payments.total() == after.borrower_view.total_payments.total()
    # assert before.borrower_view.corpus_principal.total() == after.borrower_view.corpus_principal.total()
    # assert before.borrower_view.corpus_interest.total() == after.borrower_view.corpus_interest.total()
    # assert before.borrower_view.supporter_interest.total() == after.borrower_view.supporter_interest.total()
    # assert before.borrower_view.supporter_principal.total() == after.borrower_view.supporter_principal.total()

    assert_view_is_consistent(before.borrower_view)
    assert_view_is_consistent(after.borrower_view)


def assert_total_ever_owed_has_increased(before: LoanScheduleSummary, after: LoanScheduleSummary):
    """ verify that sum of paid & remain has increased for summary and breakdown """
    assert before.borrower_view.total_payments.total() < after.borrower_view.total_payments.total()
    assert before.borrower_view.corpus_principal.total() == after.borrower_view.corpus_principal.total()
    assert before.borrower_view.corpus_interest.total() < after.borrower_view.corpus_interest.total()
    assert before.borrower_view.supporter_interest.total() < after.borrower_view.supporter_interest.total()
    assert money_matches(
        before.borrower_view.supporter_principal.total(), after.borrower_view.supporter_principal.total()
    )
    assert_view_is_consistent(before.borrower_view)
    assert_view_is_consistent(after.borrower_view)


def assert_total_ever_owed_has_decreased(before: LoanScheduleSummary, after: LoanScheduleSummary):
    """ verify that sum of paid & remain has decreased for summary and breakdown """
    assert before.borrower_view.total_payments.total() > after.borrower_view.total_payments.total()
    assert before.borrower_view.corpus_principal.total() > after.borrower_view.corpus_principal.total()
    assert before.borrower_view.corpus_interest.total() > after.borrower_view.corpus_interest.total()
    assert before.borrower_view.supporter_interest.total() > after.borrower_view.supporter_interest.total()
    assert before.borrower_view.supporter_principal.total() > after.borrower_view.supporter_principal.total()
    assert_view_is_consistent(before.borrower_view)
    assert_view_is_consistent(after.borrower_view)
