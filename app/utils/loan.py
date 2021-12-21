from enum import Enum


class Compounding(str, Enum):
    DAILY = "DAILY"


def principal_to_interest(
    principal: int, apr: float, tenor_in_days: int, compounding_frequency: Compounding = Compounding.DAILY
):
    if compounding_frequency != Compounding.DAILY:
        raise NotImplementedError("only daily compounding available for now")
    return principal * (1 + apr / 360) ** tenor_in_days - principal