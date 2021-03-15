# TODO
import pytest

from loan.loan import Loan
from loan.loan_helpers import mutate_loan
from loan.tests.conftest import regular_loans


# @pytest.mark.xfail()
def test_apr_affects_debt():
    loan_dict = regular_loans[0].copy()
    corp_apr1 = loan_dict["corp_APR"]
    loan1 = Loan(**loan_dict)
    loan2 = mutate_loan(loan_dict, "corp_APR", corp_apr1 + 0.1)
    loan3 = mutate_loan(loan_dict, "corp_APR", corp_apr1 + 0.12)
    schedule1 = loan1.summary()
    schedule2 = loan2.summary()
    schedule3 = loan3.summary()

    assert (
        schedule1.borrower_view.total_payments.remain
        < schedule2.borrower_view.total_payments.remain
        < schedule3.borrower_view.total_payments.remain
    )
    assert schedule1.next_borrower_payment < schedule2.next_borrower_payment < schedule3.next_borrower_payment


# singular matrix
@pytest.mark.xfail(strict=True)
def test_zero_supporter_apr_does_not_cause_an_error():
    loan_dict = regular_loans[0].copy()
    loan_dict["sprt_APR"] = 0
    # with pytest.raises(NotImplementedError):
    Loan(**loan_dict)


@pytest.mark.skip()
def test_collateral_affect_debts():
    pass


@pytest.mark.skip()
def test_xxxx_affects_debt():
    pass
