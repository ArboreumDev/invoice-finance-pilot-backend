from typing import Dict, List

import numpy as np
from iteround import saferound
from pydantic import BaseModel

from common.constant import DEFAULT_PRECISION_MONEY


def proportion(part, total, amount):
    """ computes part/total of amount """
    if amount == 0 or part == 0:
        return 0
    return (part / total) * amount


def safe_proportional_split(amount: float, record: Dict[str, float]):  # -> Dict[str, float]:
    """
    returns how to split up the total onto different parties,
    taking a record to indicate the respective proportions
    """
    total_shares = np.sum(list(record.values()), axis=0)
    proportions = saferound(
        {member: float(proportion(record[member], total_shares, amount)) for member in record},
        DEFAULT_PRECISION_MONEY + 4,
    )
    diff = amount - np.sum(list(proportions.values()), axis=0)
    if diff != 0:
        proportions[list(record.keys())[0]] += diff
    # assert sum(proportions.values()) == amount, f"{sum(proportions.values()) - amount}"
    return proportions


# this could use a better name for sure
def money_matches(amount1, amount2, precision=DEFAULT_PRECISION_MONEY):
    """ comparing whether the significant digits of two amounts of money are identical """
    allowed_deviation = 10 ** -precision
    if abs(amount1 - amount2) > allowed_deviation:
        # np.round(amount1, precision) == np.round(amount2, precision):
        print("amount1:", amount1)
        print("amount2:", amount2)
        print("diff:", np.abs(amount1 - amount2))
        return False
    return True


def get_list_entry(list: List[BaseModel], value: str, key="userId"):
    """
    helper function to return the first matching item of a list of pydantic-
    where the given key matches the id
    """
    return [x for x in list if x.dict()[key] == value][0]
