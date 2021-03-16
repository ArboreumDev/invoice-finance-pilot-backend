import pytest

from utils.rupeecircle_client import RupeeCircleClient, config

# from .client import RupeeCircleClient

rc_client = RupeeCircleClient(
    base_url=config["RUPEE_CIRCLE_HOSTNAME"],
    email=config["RUPEE_CIRCLE_EMAIL"],
    password=config["RUPEE_CIRCLE_PASSWORD"],
)


valid_investor_ids = [
    "INDV-21001",
    "INDV-22133" "INDV-22095",
    "INDV-22045",
    "INDV-22142",
    "INDV-22145",
    "INDV-22138",
    "INDV-22137",
    "INDV-22142",
    "INDV-22136",
    "INDV-22134",
]


def test_authenticate_valid_credentials():
    assert rc_client.headers


def test_authenticate_invalid_credentials():
    with pytest.raises(AttributeError):
        RupeeCircleClient(
            base_url=config["RUPEE_CIRCLE_HOSTNAME"],
            email="invalid@mail.org",
            password=config["RUPEE_CIRCLE_PASSWORD"],
        )

    with pytest.raises(AttributeError):
        RupeeCircleClient(
            base_url=config["RUPEE_CIRCLE_HOSTNAME"],
            email=config["RUPEE_CIRCLE_EMAIL"],
            password="deadbeef",
        )


def test_get_balances():
    res = rc_client.get_investor_balances(investor_ids=valid_investor_ids)
    assert sum(res.values())
