from typing import Dict

import pytest

from loan.loan import Loan
from loan.loan_helpers import mutate_loan
from loan.tests.conftest import some_loans
from loan.tests.helpers import (add_x_regular_repayments_to_loan,
                                   loan_is_defaulted)


@pytest.mark.parametrize("loan_dict", some_loans)
def test_partial_default(loan_dict: Dict):
    loan = add_x_regular_repayments_to_loan(Loan(**loan_dict), 3)
    loan = mutate_loan(loan_dict, "repayments", loan.repayments + [0] * (loan.tenor - 3))

    assert loan_is_defaulted(loan)


@pytest.mark.parametrize("loan_dict", some_loans)
def test_supporters_take_the_first_loss(loan_dict: Dict):
    loan = add_x_regular_repayments_to_loan(Loan(**loan_dict), 3)
    underpaid_loan = mutate_loan(loan_dict, "repayments", loan.repayments + [0])

    before = add_x_regular_repayments_to_loan(Loan(**loan_dict), 2)

    assert before.summary().corpus_view.total_receipts.paid < underpaid_loan.summary().corpus_view.total_receipts.paid


@pytest.mark.parametrize("loan_dict", some_loans)
def test_full_default(loan_dict: Dict):
    # loan = add_x_regular_repayments_to_loan(Loan(**loan_dict), 3)
    loan = mutate_loan(loan_dict, "repayments", [0] * (loan_dict["loan_tnr"]))

    assert loan_is_defaulted(loan)
