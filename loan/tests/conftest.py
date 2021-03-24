# %%
from common.constant import DEFAULT_PENALTY_APR

loan_amount = 40000
higher_loan_amount = 120000
small_loan_amount = 8000
tenor = 6
long_tenor = 12
supporter_lag = 1
default_collateral = 0
default_supporter_encumbrance_cash = 0
default_supporter_encumbrance_portfolio = 0
small_supporter_share = 0.2
high_supporter_share = 0.4
very_high_supporter_share = 0.7
corpus_apr = 0.1
supporter_apr = 0.12


tenors = [tenor, long_tenor]
amounts = [loan_amount, higher_loan_amount] #, small_loan_amount]
supporter_shares = [small_supporter_share, high_supporter_share] #, very_high_supporter_share]
apr_tuples = [(0.1, 0.1), (0.13, 0.15), (0.15, 0.1)] #, (0.05, 0.6)]

# use those if you want to focus on balloon_params
# tenors = [tenor]
# amounts = [loan_amount]
# supporter_shares = [small_supporter_share]
# apr_tuples = [(0.12, 0.15)]
# equal, supporter more, corpus more, weird values, supporter doesnt want any profit
# < lets not use the last tuple until the test for zero_supporter_apr is fixed
# apr_tuples = [(.1, .1), (.13, .15), (.15, .1), (.05, .3), (.1, 0)]

balloon_params = [None, (.5,'pct_balloon' ),  (.3, "pct_min_pmnt")]

# %%
import itertools

regular_loans = []
for tenor, loan_amount, supporter_share, aprs, b_params in list(itertools.product(tenors, amounts, supporter_shares, apr_tuples, balloon_params)):
    regular_loans.append(
        {
            "corp_APR": aprs[0],
            "sprt_APR": aprs[1],
            "loan_amt": loan_amount,
            "loan_tnr": tenor,
            "sprt_shr": supporter_share,
            "sprt_cash_encumbr": default_supporter_encumbrance_cash,
            "sprt_ptfl_encumbr": default_supporter_encumbrance_portfolio,
            "brw_collateral": default_collateral,
            "repayments": [],
            "sprt_lag": default_collateral,
            "penalty_APR": DEFAULT_PENALTY_APR,
            "balloon_params": b_params
        }
    )

# some_loans = regular_loans[1::8]
some_loans = regular_loans
# some_loans = regular_loans[:1]

# %%

# @gsVam
# definec different kinds of coupons here
# coupons = [generateCoupon(...) for params in paramCombinations]
coupons = []
