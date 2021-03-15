import pytest


@pytest.mark.skip()
def test_repayment_with_encumrbances():
    # should not increase supporter balances (as dissolved is kept in escrow for a bit? need help on the logic here!)
    # should dissolve supporter encumbrances (GAURAV, right from the first repayment or only the second)
    # encumbrances should be resolved
    raise NotImplementedError
