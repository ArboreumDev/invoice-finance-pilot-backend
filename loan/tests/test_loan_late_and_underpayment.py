from typing import Dict

import pytest

from loan.loan import Loan
from loan.loan_helpers import mutate_loan
from loan.tests.conftest import some_loans
from loan.tests.helpers import (add_x_regular_repayments_to_loan,
                                   assert_underpayment_registered_correctly,
                                   complete_loan_with_regular_payments,
                                   loan_is_repaid)


# underpayment does not cause total owed to go up => issue 214
@pytest.mark.xfail()
@pytest.mark.parametrize("loan_dict", some_loans)
@pytest.mark.parametrize("underpayment", [0, 1000])
def test_underpayments_as_first_payments_increase_debt(loan_dict: Dict, underpayment: int):
    # print(len(list(itertools.product(some_loans[:2], [0, 1000]))))
    before = Loan(**loan_dict)
    after = mutate_loan(loan_dict, "repayments", [underpayment])
    assert_underpayment_registered_correctly(before, after, underpayment)


# underpayment does not cause total owed to go up => 124
@pytest.mark.xfail()
@pytest.mark.parametrize("loan_dict", some_loans)
@pytest.mark.parametrize("underpayment", [0, 1000])
def test_underpayments_as_second_payments_increase_debt(loan_dict: Dict, underpayment: int):
    before = add_x_regular_repayments_to_loan(Loan(**loan_dict), 1)
    last_payment = before.repayments[-1]

    after = mutate_loan(loan_dict, "repayments", [last_payment, underpayment])
    assert_underpayment_registered_correctly(before, after, underpayment)


# same errors as regular repayments: final schedule doesnt add up
@pytest.mark.parametrize("loan_dict", some_loans)
@pytest.mark.parametrize("underpayment", [0, 1000])
def test_loan_can_be_completed_after_underpayment(loan_dict: Dict, underpayment: int):
    loan = Loan(**loan_dict)
    loan.calc_schedule(loan.repayments + [underpayment])
    after = complete_loan_with_regular_payments(loan)
    assert loan_is_repaid(after)
