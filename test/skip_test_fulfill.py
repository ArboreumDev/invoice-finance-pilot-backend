import pprint
from collections import Counter, defaultdict
from typing import Any, Dict

import numpy as np
import scipy as sp
from utils.fullfill_loan import fulfill


# %% define test helpers
def parse_contrib_dict(contributions):
    """
    Parameters
    ----------
    contributions: dict of dicts {LenderID:{BorrowerID:Amount},...}

    Returns
    -------
    loan_requests: dict {BorrowerID:Amount,...}
    lender_contrib: dict of dicts {BorrowerID:{LenderID:Amount}}
    """

    # parse loan_requests from contributions
    loan_requests = {}
    prv_contrib = {}
    for lender_id, contrib_dict in contributions.items():
        prv_contrib[lender_id] = sum(contrib_dict.values())
        for brw_id, contrib_amt in contrib_dict.items():
            if brw_id in loan_requests:
                loan_requests[brw_id] += contrib_amt
            else:
                loan_requests[brw_id] = contrib_amt

    # invert the prv contributions dict
    lender_contrib = defaultdict(dict)
    for key, val in contributions.items():
        for subkey, subval in val.items():
            lender_contrib[subkey][key] = subval

    return loan_requests, lender_contrib


def test_fulfill_quality(
    prv_contributions: Dict[Any, float], start_balances: Dict[Any, float], update_balances: Any = None
):

    # update starting day balances
    if update_balances is not None:
        start_balances.update(update_balances)

    # parse loan_requests from contributions
    loan_requests, lender_contrib = parse_contrib_dict(prv_contributions)

    for id, loan_amount in loan_requests.items():
        # optimal new lender balances
        contrib, new_balance_opt = fulfill(loan_amount, start_balances)

        # actual new lender balances
        new_balance_act = Counter(start_balances)
        new_balance_act.subtract(Counter(lender_contrib[id]))

        # compute cosine distance
        dist = sp.spatial.distance.cosine(list(new_balance_opt.values()), list(new_balance_act.values()))

        if dist > 0.1:
            print("for BorrowerID " + str(id) + " significant difference between actual vs optimal")
            print("Optimal:")
            pprint({x: y for x, y in contrib.items() if y != 0})
            print("Actual")
            pprint(lender_contrib[id])
        else:
            print("optimal and actual are sufficiently close for BorrowerID " + str(id))


# %% Test if edge case works
def test_edge_case():
    # tests case where all rest is 0 except one option
    contrib, new_balances = fulfill(100000, {1: 50000, 2: 25000, 3: 10000, 4: 10000, 5: 20000, 6: 5000, 7: 5000})
    # check if balance for lender 1 is 25000
    assert new_balances[1] == 25000
    # check if rest are 0
    assert sum(list(new_balances.values())[1:]) == 0


test_edge_case()

# %% Test if failure is as desired
def test_failure_case():
    balances = {1: 20000, 2: 25000, 3: 10000, 4: 10000, 5: 20000, 6: 5000, 7: 5000}
    # tests case where all rest is 0 except one option
    contrib, new_balances = fulfill(100000, balances)
    # check if contributions are nan
    assert np.isnan(sum(list(contrib.values())))
    # check if rest are 0
    assert new_balances == balances


test_failure_case()

# %% Day 1- 4th Dec 2020
start_balances = {
    "Rohit": 96138,
    "Sanjay": 7138,
    "Avinash": 12000,
    "Renu": 12138,
    "Ninisha": 7000,
    "Prateek": 57000,
    "Mehul": 77000,
    "Mohan": 8000,
    "Naushil": 50000,
    "Pushkar": 0,
    "Amit": 0,
    "Ravi": 0,
    "Sharath": 0,
    "Prashanth": 0,
    "Gautam": 0,
    "Ankit": 0,
}

day1_contrib = {
    "Rohit": {53602: 5000, 53611: 12000, 53609: 10000, 53610: 10000},
    "Sanjay": {53602: 1000},
    "Renu": {53602: 1000},
    "Prateek": {53602: 5000, 53611: 12000, 53609: 10000, 53610: 10000},
    "Mehul": {53602: 5000, 53611: 12000, 53609: 10000, 53610: 10000},
    "Naushil": {53602: 5000, 53611: 12000, 53609: 10000, 53610: 10000},
}

test_fulfill_quality(day1_contrib, start_balances)

# %% Day 2- 5th Dec 2020
update_balances = {
    "Rohit": 59138,
    "Sanjay": 56138,
    "Avinash": 12000,
    "Renu": 61138,
    "Ninisha": 7000,
    "Prateek": 70000,
    "Mehul": 120000,
    "Mohan": 158000,
    "Naushil": 13000,
}

day2_contrib = {
    "Rohit": {1: 20000, 2: 14000, 3: 12000, 4: 5000},
    "Sanjay": {1: 4000, 3: 15000, 4: 10000},
    "Avinash": {1: 4000, 2: 3000, 3: 3000, 4: 1000},
    "Renu": {1: 4000, 2: 3000, 3: 15000, 4: 12000},
    "Prateek": {1: 8000, 2: 7000, 3: 2000, 4: 18000},
    "Mehul": {1: 16000, 2: 12000, 3: 5000, 4: 5000},
    "Mohan": {1: 20000, 2: 14000, 3: 18000, 4: 18000},
    "Naushil": {1: 4000, 2: 3000, 3: 3000, 4: 2000},
}

test_fulfill_quality(day2_contrib, start_balances, update_balances)
