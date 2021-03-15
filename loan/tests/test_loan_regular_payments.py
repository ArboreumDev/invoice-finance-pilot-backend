import pytest

from loan.loan import Loan
from loan.tests.conftest import regular_loans, some_loans
from loan.tests.helpers import (
    add_x_regular_repayments_to_loan,
    assert_timely_repayment_registered_correctly, loan_is_repaid)
from utils.helpers import money_matches


# any test loan with supporter_apr leads to singular matrix with error
@pytest.mark.parametrize("loan_dict", regular_loans)
def test_init_loan_class(loan_dict):
    Loan(**loan_dict)


@pytest.mark.parametrize("loan_dict", some_loans)
def test_first_regular_repayment(loan_dict):
    before = Loan(**loan_dict)
    after = add_x_regular_repayments_to_loan(Loan(**loan_dict), 1)

    assert_timely_repayment_registered_correctly(before, after, after.repayments[-1])

    # money goes into escrow
    assert after.escrow > 0 and before.escrow == 0

    # loan state is live
    assert before.status == after.status == "live"


@pytest.mark.parametrize("loan_dict", some_loans)
def test_second_regular_repayment(loan_dict):
    after_first = add_x_regular_repayments_to_loan(Loan(**loan_dict), 1)
    after_second = add_x_regular_repayments_to_loan(Loan(**loan_dict), 2)

    assert_timely_repayment_registered_correctly(after_first, after_second, after_second.repayments[-1])
    assert after_second.status == after_first.status == "live"


@pytest.mark.parametrize("loan_dict", some_loans)
def test_state_before_last_regular_repayment(loan_dict):
    before_last = add_x_regular_repayments_to_loan(Loan(**loan_dict), loan_dict["loan_tnr"] - 1)
    assert before_last.status == "live"

    # verify that full single repay is the same as regular amount
    summary = before_last.summary()
    assert money_matches(summary.next_borrower_payment, summary.full_single_repay, 1)
    # assert money_matches(summary.next_borrower_payment == summary


# schedule doesnt check out in the final state
@pytest.mark.parametrize("loan_dict", some_loans)
def test_complete_loan_with_regular_payments(loan_dict):
    after = add_x_regular_repayments_to_loan(Loan(**loan_dict), loan_dict["loan_tnr"])
    if not loan_is_repaid(after):
        print(1)

    assert loan_is_repaid(after)


@pytest.mark.parametrize("loan_dict", some_loans)
def test_complete_loan_with_immediate_early_repayment(loan_dict):
    loan = Loan(**loan_dict)
    full_repayment = loan.summary().full_single_repay
    loan.calc_schedule([full_repayment])

    assert loan_is_repaid(loan)


@pytest.mark.parametrize("loan_dict", some_loans)
def test_complete_loan_with_early_repayment_after_one_regular_repayment(loan_dict):
    loan = add_x_regular_repayments_to_loan(Loan(**loan_dict), 1)
    full_repayment = loan.summary().full_single_repay
    loan.repayments.append(full_repayment)
    loan.calc_schedule()

    assert loan_is_repaid(loan)


@pytest.mark.parametrize("loan_dict", some_loans[3:4])
def test_complete_loan_with_early_repayment_after_two_regular_repayments(loan_dict):
    loan = add_x_regular_repayments_to_loan(Loan(**loan_dict), 2)
    full_repayment = loan.summary().full_single_repay
    loan.repayments.append(full_repayment)
    loan.calc_schedule()

    assert loan_is_repaid(loan)
