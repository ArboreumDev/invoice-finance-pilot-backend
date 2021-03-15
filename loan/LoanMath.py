import datetime as dt
from typing import List

import numpy as np
from scipy import optimize, special

from common.constant import DEFAULT_DISCOUNT_APR
from common.loan import Repayment
from loan.coupon import Coupon


class LoanMath:
    @classmethod
    def convert_regular_payments_to_sequence(
        payments: List[Repayment], start_date: dt.datetime, days_per_period: int = 30
    ):
        """
        convert a list of payment-date-tuples into a simple array,
        with all payments from the same period added up into one
        """
        sorted_payments_by_date = sorted(payments, key=lambda x: x[0])
        as_sequence = [0]
        active_period_start_date = start_date
        while sorted_payments_by_date:
            c_date, c_amount = sorted_payments_by_date.pop(0)
            while active_period_start_date + dt.timedelta(days=days_per_period) <= c_date:
                active_period_start_date += dt.timedelta(days=days_per_period)
                as_sequence.append(0)
            as_sequence[-1] += c_amount
        return as_sequence

    @classmethod
    def convert_regular_payments_to_prd_indx_dict(
        payments: List[Repayment], start_date: dt.datetime, days_per_period: int = 30
    ):
        """
        convert a list of payment-date-tuples into a dict as so {period: amount},
        with all payments from the same period added up into one
        """
        # parse payment tuple
        parsed = [list(t) for t in zip(*payments)]
        dates = parsed[0]
        payments = parsed[1]

        # convert dates to index
        date_indx = [int(np.floor((date - start_date).days / days_per_period)) for date in dates]

        # coalesce in case multiple payments in period
        pmnt_date_list = list(zip(date_indx, payments))
        coalesced = [
            [k, sum(v for _, v in g)] for k, g in groupby(sorted(pmnt_date_list), key=lambda x: x[0])  # noqa:  F821
        ]

        return {item[0]: item[1] for item in coalesced}

    @staticmethod
    def calc_IRR_NPV(
        loan_amt: float,
        loan_tnr: float,
        APR: float,
        discount_APR: float = DEFAULT_DISCOUNT_APR,
        prv_pmnts: List[float] = [],
        annual_cmpnd_prds: int = 12,
    ):
        """
        calculates IRR and NPV for a constant annuity

        Parameters
        ----------
        loan_amt (float): principal
        loan_tnr (float): number of periods
        APR (float) : annual percentage interest rate
        discount_APR (float): annual discount rate
        prv_pmnts (list): previous payments
        annual_cmpnd_prds (int): number annual compound periods

        Returns
        -------
        IRR (float: Internal-rate of return of annuity
        NPV (float): net-present value of annuity
        """

        # period percentage rate
        dscnt_rate = discount_APR / annual_cmpnd_prds

        # calculate coupon
        if len(prv_pmnts) < loan_tnr:
            coupon = Coupon(
                prcp_corp=0,
                prcp_sprt=loan_amt,
                APR_corp=APR,
                APR_sprt=APR,
                loan_tnr=loan_tnr,
                prv_pmnts_corp=[0] * len(prv_pmnts),
                prv_pmnts_sprt=prv_pmnts,
                max_slope=0,
                annual_cmpnd_prds=annual_cmpnd_prds,
            ).to_dict()

            ideal_payments = coupon["sprt_collections"]
        else:
            ideal_payments = prv_pmnts

        # get first period length
        fst_prd_len = loan_tnr % 1
        if fst_prd_len == 0:
            fst_prd_len = 1
        loan_tnr = np.ceil(loan_tnr).astype(int)

        # previous payments must discounted by the interest owed
        discount = np.array([(1 + dscnt_rate) ** (t + fst_prd_len) for t in range(0, len(ideal_payments))])

        # calculate NPV and IRR
        NPV = np.sum(ideal_payments / discount)  # calc NPV of payments
        IRR = NPV / loan_amt - 1

        return IRR, NPV

    @staticmethod
    def calc_APR_NPV(
        loan_amt: float,
        loan_tnr: float,
        IRR: float,
        discount_APR: float = DEFAULT_DISCOUNT_APR,
        prv_pmnts: List[float] = [],
        annual_cmpnd_prds: int = 12,
    ):
        """
        calculates APR and NPV for a desired IRR (optimizer outputs APR)

        Parameters
        ----------
        loan_amt (float): principal
        loan_tnr (float): number of periods
        IRR (float) : desired internal rate of return (decimal)
        discount_APR (float): annual discount rate
        prv_pmnts (list): previous payments
        annual_cmpnd_prds (int): number annual compound periods

        Returns
        -------
        APR (float: APR to charge on annuity
        NPV (float): net-present value of annuity
        """

        # being lazy and brute-force solving it
        def function_2_solve(APR):
            IRR_hat, NPV = LoanMath.calc_IRR_NPV(loan_amt, loan_tnr, APR[0], discount_APR, prv_pmnts, annual_cmpnd_prds)
            return IRR_hat - IRR

        # Find Roots
        init_guess = discount_APR * 2 + IRR
        APR = optimize.fsolve(function_2_solve, init_guess)

        IRR_new, NPV = LoanMath.calc_IRR_NPV(loan_amt, loan_tnr, APR[0], discount_APR, prv_pmnts, annual_cmpnd_prds)

        return APR[0], NPV

    @staticmethod
    def calc_firstLoss_pct_val(
        pr_kum_loan: List[float], init_collateral: float, corp_prcp_outstand: float, sprt_prcp_outstand: float
    ):
        """
        Parameters
        ----------
        pr_kum_loan ([float,float]): kumararaswamy alpha and beta parameters of Loan's risk distribution
        init_collateral (float): initial collateral on loan
        corp_prcp_outstand (float): corpus (senior tranche) outstanding principal
        sprt_prcp_outstand (float): supporter (junior tranche) oustanding principal

        Returns
        -------
        (float) the value (in terms of the area of the CDF) of the first loss guarantee provided by the supporter
        """

        # ratio supporter principal to total
        v_sprt = sprt_prcp_outstand / (corp_prcp_outstand + sprt_prcp_outstand)

        # expected value of borrower first loss
        E_loss = lambda a, b, x: 1 - b * special.betainc((1 + 1 / a), b, x ** a)  # noqa: E731

        # collateral from first loss
        c_loss = E_loss(pr_kum_loan[0], pr_kum_loan[1], (1 - init_collateral) * (1 - v_sprt)) - E_loss(
            pr_kum_loan[0], pr_kum_loan[1], (1 - init_collateral)
        )

        return c_loss
