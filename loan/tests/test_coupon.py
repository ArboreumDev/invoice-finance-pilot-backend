import pytest
from loan.tests.conftest import coupons
from typing import Tuple, Dict
from loan.couponTypes import generate_coupon


@pytest.mark.parametrize("coupon_params", coupons)
def test_coupon_init(coupon_params: Dict):
    c = generate_coupon(**coupon_params)
    # assert stuff
    pass


# or initialize like this:
@pytest.mark.parametrize("balloon_params", ["""TODO add params here"""])
@pytest.mark.parametrize("terms", [(12,1), (360,30)])
def test_some_other_property(terms: Tuple[int,int], balloon_params: any):
    # do stuff
    # assert stuff
    pass
