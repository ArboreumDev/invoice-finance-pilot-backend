import copy
import logging
from typing import List, Dict, Any, Tuple

import numpy as np
import pandas as pd
import datetime as dt

from common.constant import (DEFAULT_DISCOUNT_APR,
                                     DEFAULT_PRECISION_MATH_OPERATIONS,
                                     DEFAULT_PRECISION_MONEY,
                                     DEFAULT_SUPPORTER_LAG)
from common.exceptions import InternalError
from common.loan import LoanScheduleSummary
from common.system import PaymentSplit, RepaymentBreakdown
from common.util import APR
from loan.baseloan import BaseLoan
from loan.couponTypes import generate_coupon
from loan.LoanMath import LoanMath

logging.basicConfig(filename="loan_schedule.log", level=logging.DEBUG)

# TODO: #183 add credit-line loan schedule
class Loan(BaseLoan):
    def __init__(
        self,
        corp_APR: float,
        sprt_APR: float,
        loan_amt: float,
        loan_tnr: float,
        sprt_shr: float,
        sprt_cash_encumbr: float,
        sprt_ptfl_encumbr: float,
        brw_collateral: float,
        repayments: List[float],
        penalty_APR: float,
        sprt_lag: int = DEFAULT_SUPPORTER_LAG,
        discount_APR: float = DEFAULT_DISCOUNT_APR,
        subsprt_info: Dict={},
        balloon_params: Any = (0.5,'pct_balloon'), 
        max_slope: float = np.inf,
        annual_cmpnd_prds: int = 12,
        collection_freq: int = 1,
        collection_dates: List[dt.datetime] = [],
        id="",
    ):
        """
        The Loan represents the atomistic unit of all debt in our system--all debt is mapped to a loan
        and all loans are dispersed to many lenders. In Loan we take the coupon and layer on the "idiosyncratic"
        parameters of borrower collateral, encumbrances of the supporter, etc to product the final loan schedule

        Parameters
        ----------
        corp_APR     (float): annual percentage rate for corpus as decimal, in [0,1]
        sprt_APR     (float): annual percentage rate for supporters in [0,1]
        loan_amt     (float): loan amount
        loan_tnr     (float): loan tenor (non integer number indicates first period length < 1)
        sprt_shr     (float): share of principal that supporters have taken on, in [0,1]
        sprt_cash_encumbr (float): amount of cash supporters have encumbered as collateral towards loan
        sprt_ptfl_encumbr (float): amount of portfolio supporters have encumbered as collateral towards loan
        brw_collateral (float): amount of collateral borrower is bringing to loan
        repayments ([float]): vector of payments borrower has made on loan
        penalty_APR  (float): addition to APR for late payments (not implemented yet), in [0,1]
        sprt_lag       (int): lag in payments to supporters
        discount_APR (float): discount rate, [0,1]
        subsprt_info (Dict): Loans can be stacked into multiple tranches through this parameter (see coupon.pu)
        balloon_params (Any): Loan can have a balloon payment, this is parameterized by a tuple with the appropriate parameters
                              or a float value <1  and a string indicating if it represents the %principal of the balloon payment
                              or the % of the principal that the minimum payment per month should be til the end
        max_slope (float): max allowable slope that payment adjusts between tranches
                           (can set to 0 if want vanilla schedule)
        annual_cmpnd_prds (int):  number of compounding periods per year of 360 days (i.e 360=daily compounding)
        collection_freq (int): number compounding periods per collection (e.g. 30 if daily compounding and monthly collection),
        collection_dates (List[dt.datetime]): collection dates for repayments, first date in list should be disbursal data
        id (Any): unique ID of Loan,

        Methods
        -------
        calc_schedule : at the heart of the clss, computes the schedule(automatically executed when repayments is non-empty)
        update (repayments) : use this method to update the object when new repayments occur
        summarize_schedule (actor): produces a dataframe with summary info for the various actors of the loan (borrower, supporter lenders, corpus lenders)
        fetch_repayment_amount (period or date): given a period or date (if loan was parameterized with repayment dates) gives the amount due, and full repay
        """

        BaseLoan.__init__(self, loan_amount=loan_amt, tenor=loan_tnr, repayments=repayments, id=id)

        # self._logger = logging.getLogger(self.__class__.__name__)

        # significant figures to round
        self.sig_figs_2rnd = DEFAULT_PRECISION_MATH_OPERATIONS

        # if loan tenor not an integer than implies the first period has some length<1
        self.loan_tnr = int(np.ceil(loan_tnr))
        self.orig_loan_tnr = loan_tnr
        self.sprt_lag = max(1, sprt_lag)  # this minimum needs to be 1 for now (0 handled a bit differently)
        self.corp_APR = corp_APR
        self.sprt_APR = sprt_APR
        self.discount_APR = discount_APR
        self.loan_amt = loan_amt
        self.sprt_shr = sprt_shr
        self.sprt_cash_encumbr = sprt_cash_encumbr
        self.sprt_ptfl_encumbr = sprt_ptfl_encumbr
        self.brw_collateral = brw_collateral

        # info needed only for coupon
        self.penalty_APR = penalty_APR
        self.annual_cmpnd_prds = annual_cmpnd_prds
        self.max_slope = max_slope
        self.collection_freq = collection_freq
        self.subsprt_info = subsprt_info
        self.balloon_params = balloon_params
        self.collection_dates = collection_dates

        # initial coupon terms (this is what should happen if all borrower pays according to pmnt_init every period)
        self.corp_prcp_outstand_init = loan_amt * (1 - sprt_shr)
        self.sprt_prcp_outstand_init = loan_amt * (sprt_shr)

        # initialize coupon (core math logic here)
        self._init_coupon()

        # initalize schedule
        self.repayments = []  # [repayments]
        self.prv_repayments = []  # copy.copy(repayments)
        self.amt_repaid = 0  # np.sum(repayments)  # total amount repaid
        self.prds_concld = 0  # len(repayments)  # periods concluded
        self.prds_remain = self.loan_tnr - self.prds_concld  # periods remaining
        self._init_pmnt_schedule()
        self._init_allocation_tbl()
        
        # initial payment
        self.pmnt_init = self.coupon.corp_collect_current + self.coupon.sprt_collect_current

        # vectors for storing state
        self.sprt_ptfl_on_hand = np.full(self.loan_tnr + 1, np.nan)
        self.sprt_cash_on_hand = np.full(self.loan_tnr + 1, np.nan)
        self.sprt_pmnt_on_hand = np.full(self.loan_tnr + 1, np.nan)
        self.sprt_ptfl_on_hand[0] = self.sprt_ptfl_encumbr  # encumbered portfolio available
        self.sprt_cash_on_hand[0] = self.sprt_cash_encumbr  # encumbered cash available
        self.sprt_pmnt_on_hand[0] = 0

        # re-calculate loan schedule with repayments
        if repayments:
            self.update(repayments)
        else:
            self.pmnt_curr = self.schedule_DF.loc["brw_2pay_ideal", (self.prds_concld + 1)]
            self.full_single_repay = self.schedule_DF.loc["brw_2pay_finish", (self.prds_concld + 1)]
            self.brw_overpay = 0

        # self._logger.info("Instantiated")
        # self._logger.info(vars(self))

    def _init_coupon(self,prv_pmnts_corp=[],prv_pmnts_sprt=[]):
        """
        initializes the coupon object that is the brains of the Loan
        
        Parameters
        ----------
        prv_pmnts_corp (List[float]): all previous payments to the corpus tranche
        prv_pmnts_sprt (List[float]): all previous payments to the supporter tranche

        Returns 
        -------
        sets coupon object, returns nothing
        """
        
        if self.balloon_params is not None:
            self.coupon_type = 'balloon'
        else:
            self.coupon_type = 'standard'

        # initialize coupon (core math logic here)  
        self.coupon = generate_coupon(
                prcp_corp=self.loan_amt * (1 - self.sprt_shr),
                prcp_sprt=self.loan_amt * (self.sprt_shr),
                APR_corp=self.corp_APR,
                APR_sprt=self.sprt_APR,
                loan_tnr=self.orig_loan_tnr,
                prv_pmnts_corp=prv_pmnts_corp,
                prv_pmnts_sprt=prv_pmnts_sprt,
                balloon_params = self.balloon_params,
                APR_pnlt=self.penalty_APR,
                max_slope=self.max_slope,
                subsprt_info=self.subsprt_info,
                sig_figs_2rnd=self.sig_figs_2rnd,
                annual_cmpnd_prds=self.annual_cmpnd_prds,
                collection_freq=self.collection_freq,
                collection_dates=self.collection_dates,
                coupon_type = self.coupon_type)
    
    def _init_pmnt_schedule(self):
        """
        initializes the dataframe with the loan schedule

        Returns 
        -------
        sets schedule_DF, returns nothing
        """

        # dataframe to store payment schedule
        pmntTypes = [
            "brw_2pay_finish",
            "brw_2pay_ideal",
            "corp_prcp_2pay_ideal",
            "corp_intr_2pay_ideal",
            "corp_pnlt_2pay_ideal",  # note that penalty is included in interest
            "sprt_prcp_2pay_ideal",
            "sprt_intr_2pay_ideal",
            "sprt_pnlt_2pay_ideal",
            "brw_paid_actual",
            "corp_paid_actual",
            "sprt_paid_withheld",
            "sprt_2pay_now",
            "corp_prcp_paid_actual",
            "corp_intr_paid_actual",
            "sprt_prcp_paid_actual",
            "sprt_intr_paid_actual",
            "corp_prcp_outstand_4brw",
            "corp_prcp_outstand_4corp",
            "corp_intr_outstand_4brw",
            "corp_intr_outstand_4corp",
            "sprt_prcp_outstand_4brw",
            "sprt_prcp_outstand_4sprt",
            "sprt_intr_outstand_4brw",
            "sprt_intr_outstand_4sprt",
            "corp_IRR",
            "sprt_IRR",
            "totl_IRR",
            "sprt_cash_unencumbr",
            "sprt_cash_send2corp",
            "sprt_cash_remain",
            "sprt_cash_used",
            "sprt_cash_rtrn",
            "sprt_ptfl_unencumbr",
            "sprt_ptfl_send2corp",
            "sprt_ptfl_remain",
            "sprt_ptfl_used",
            "sprt_ptfl_rtrn",
            "sprt_pmnt_send2corp",
            "sprt_pmnt_remain",
            "sprt_pmnt_used",
            "sprt_pmnt_rtrn",
            "brw_colt_send2corp",
            "brw_colt_send2sprt",
            "brw_colt_remain",
            "brw_colt_used",
        ]
        schedule_DF = pd.DataFrame(
            np.full([len(pmntTypes), min(self.loan_tnr + 1, self.prds_concld + 2)], np.NaN),
            index=pmntTypes,
            columns=range(0, min(self.loan_tnr + 1, self.prds_concld + 2)),
        ).astype("float64")

        schedule_DF.at["corp_intr_2pay_ideal", 0] = 0
        schedule_DF.at["corp_prcp_2pay_ideal", 0] = 0
        schedule_DF.at["sprt_intr_2pay_ideal", 0] = 0
        schedule_DF.at["sprt_prcp_2pay_ideal", 0] = 0
        schedule_DF.at["corp_pnlt_2pay_ideal", 0] = 0
        schedule_DF.at["sprt_pnlt_2pay_ideal", 0] = 0
        schedule_DF.at["brw_2pay_ideal", 0] = 0
        schedule_DF.at["brw_2pay_finish", 0] = self.loan_amt

        schedule_DF.at["sprt_cash_unencumbr", 0] = 0
        schedule_DF.at["sprt_cash_send2corp", 0] = 0
        schedule_DF.at["sprt_cash_remain", 0] = self.sprt_cash_encumbr
        schedule_DF.at["sprt_cash_used", 0] = 0
        schedule_DF.at["sprt_cash_rtrn", 0] = 0
        schedule_DF.at["sprt_ptfl_unencumbr", 0] = 0
        schedule_DF.at["sprt_ptfl_send2corp", 0] = 0
        schedule_DF.at["sprt_ptfl_remain", 0] = self.sprt_ptfl_encumbr
        schedule_DF.at["sprt_ptfl_used", 0] = 0
        schedule_DF.at["sprt_ptfl_rtrn", 0] = 0
        schedule_DF.at["sprt_pmnt_send2corp", 0] = 0
        schedule_DF.at["sprt_pmnt_remain", 0] = 0
        schedule_DF.at["sprt_pmnt_used", 0] = 0
        schedule_DF.at["sprt_pmnt_rtrn", 0] = 0
        # we only use the borrower collateral at the last period to return principal to lenders
        schedule_DF.at["brw_colt_send2corp", :] = 0
        schedule_DF.at["brw_colt_send2sprt", :] = 0
        schedule_DF.at["brw_colt_remain", :] = self.brw_collateral
        schedule_DF.at["brw_colt_used", :] = 0

        self.schedule_DF = schedule_DF
        self._update_schedule_from_coupon(0)

    def _init_allocation_tbl(self):
        """
        initializes the allocation table where incoming funds are allocated in descending order according
        to the indx variable in this function (i.e. funds cascade downwards filling each bucket)
        see fill_helper function to understand more
        
        Returns
        -------
        allocate_DF
        """
        # Create dataframe to store allocation results (simply called df for now)
        indx = [
            "corp_prcp_backlog",
            "corp_prcp_current",
            "sprt_ptfl_owed_bklg",
            "sprt_ptfl_owed_curr",
            "sprt_cash_owed_bklg",
            "sprt_cash_owed_curr",
            "sprt_pmnt_backlog",
            # these represent the three guarantees the supporter brings (portfolio, cash, witheld payment)
            "sprt_prcp_backlog",
            "sprt_prcp_current",
            "corp_intr_backlog",
            "corp_intr_current",
            "sprt_intr_backlog",
            "sprt_intr_current",
            "brw_collateral_owed_curr",
            "sprt_cash_unencumbr_bklg",
            "sprt_cash_unencumbr_curr",
            "sprt_ptfl_unencumbr_bklg",
            "sprt_ptfl_unencumbr_curr",
        ]

        df = pd.DataFrame(np.full([len(indx), (self.prds_concld + 1) * 2], 0), index=indx).astype("float64")
        df.columns = pd.MultiIndex.from_product([np.arange(1, self.prds_concld + 2), ["owed", "filled"]])

        # set initial allocation values for first repayment period
        df.at["corp_prcp_current", (1, "owed")] = self.schedule_DF.loc["corp_prcp_2pay_ideal", 1]
        df.at["sprt_prcp_current", (1, "owed")] = self.schedule_DF.loc["sprt_prcp_2pay_ideal", 1]
        df.at["corp_intr_current", (1, "owed")] = self.schedule_DF.loc["corp_intr_2pay_ideal", 1]
        df.at["sprt_intr_current", (1, "owed")] = self.schedule_DF.loc["sprt_intr_2pay_ideal", 1]
        df.at["sprt_ptfl_owed_curr", (1, "owed")] = self.sprt_ptfl_encumbr  # portfolio encumbrance
        df.at["sprt_cash_owed_curr", (1, "owed")] = self.sprt_cash_encumbr  # cash encumbrance

        self.allocate_DF = df

    def _update_schedule_from_coupon(self, indx, finalize=False):
        """
        updates the schedule for the period set by indx (period 1 = indx 1)
        usually coupon object is newly updated before this is called

        Parameters
        ----------
        indx (int): period of loan
        """

        # function to help calculate IRR
        def IRR_helper(all_exp_payments, APR, principal):
            IRR, NPV = LoanMath.calc_IRR_NPV(
                principal,
                self.loan_tnr,
                APR=APR,
                discount_APR=self.discount_APR,
                prv_pmnts=all_exp_payments,  # [0:self.loan_tnr],
                annual_cmpnd_prds=self.annual_cmpnd_prds,
            )
            return IRR

        if finalize:
            indx += -1

        # update IRR
        self.schedule_DF.at["corp_IRR", indx] = \
            IRR_helper(self.coupon.corp_pmnt_perCollect, self.corp_APR, self.loan_amt * (1 - self.sprt_shr))
        self.schedule_DF.at["sprt_IRR", indx] = \
            IRR_helper(self.coupon.sprt_pmnt_perCollect, self.sprt_APR, self.loan_amt * (self.sprt_shr))
        self.schedule_DF.at["totl_IRR", indx] = \
            IRR_helper(self.coupon.corp_pmnt_perCollect + self.coupon.sprt_pmnt_perCollect, 0, self.loan_amt)

        # set outstanding principal
        self.schedule_DF.at["corp_prcp_outstand_4brw", indx] = self.coupon.corp_prcp_owed
        self.schedule_DF.at["sprt_prcp_outstand_4brw", indx] = self.coupon.sprt_prcp_owed
        if indx == 0:
            self.schedule_DF.at["corp_prcp_outstand_4corp", indx] = self.coupon.corp_prcp_owed
            self.schedule_DF.at["sprt_prcp_outstand_4sprt", indx] = self.coupon.sprt_prcp_owed
        else:
            self.schedule_DF.at["corp_prcp_outstand_4corp", indx] = \
                self.schedule_DF.at["corp_prcp_outstand_4corp", (indx - 1)] \
                - self.schedule_DF.at["corp_prcp_paid_actual", indx]
            
            self.schedule_DF.at["sprt_prcp_outstand_4sprt", indx] = \
                self.schedule_DF.at["sprt_prcp_outstand_4sprt", (indx - 1)] \
                - self.schedule_DF.at["sprt_prcp_paid_actual", indx]

        # update outstanding interest and principal to observe limits
        if self.schedule_DF.at["corp_prcp_outstand_4corp", indx] < 0:
            self.schedule_DF.at["corp_intr_outstand_4corp", indx] += -self.schedule_DF.at["corp_prcp_outstand_4corp", indx]
            self.schedule_DF.at["corp_prcp_outstand_4corp", indx] = 0
        if self.schedule_DF.at["sprt_prcp_outstand_4sprt", indx] < 0:
            self.schedule_DF.at["sprt_intr_outstand_4sprt", indx] += -self.schedule_DF.at["sprt_prcp_outstand_4sprt", indx]
            self.schedule_DF.at["sprt_prcp_outstand_4sprt", indx] = 0
        if self.schedule_DF.at["corp_intr_outstand_4corp", indx] < 0:
            self.schedule_DF.at["corp_prcp_outstand_4corp", indx] += self.schedule_DF.at["corp_intr_outstand_4corp", indx]
            self.schedule_DF.at["corp_intr_outstand_4corp", indx] = 0
        if self.schedule_DF.at["sprt_intr_outstand_4sprt", indx] < 0:
            self.schedule_DF.at["sprt_prcp_outstand_4sprt", indx] += self.schedule_DF.at["sprt_intr_outstand_4sprt", indx]
            self.schedule_DF.at["sprt_intr_outstand_4sprt", indx] = 0

        # set outstanding interest
        self.schedule_DF.at["corp_intr_outstand_4brw", indx] = self.coupon.corp_intr_owed
        self.schedule_DF.at["sprt_intr_outstand_4brw", indx] = self.coupon.sprt_intr_owed
        self.schedule_DF.at["corp_intr_outstand_4corp", indx] = self.schedule_DF.at["corp_intr_outstand_4brw", indx] \
                                                                + self.schedule_DF.at["corp_prcp_outstand_4brw", indx] \
                                                                - self.schedule_DF.at["corp_prcp_outstand_4corp", indx]
        self.schedule_DF.at["sprt_intr_outstand_4sprt", indx] = self.schedule_DF.at["sprt_intr_outstand_4brw", indx] \
                                                                + self.schedule_DF.at["sprt_prcp_outstand_4brw", indx] \
                                                                - self.schedule_DF.at["sprt_prcp_outstand_4sprt", indx]
        
        if indx < self.loan_tnr:
            # expected payments for next period
            self.schedule_DF.at["corp_prcp_2pay_ideal", indx + 1] = self.coupon.corp_prcp_perCollect[indx]
            self.schedule_DF.at["corp_intr_2pay_ideal", indx + 1] = self.coupon.corp_intr_perCollect[indx]
            self.schedule_DF.at["sprt_prcp_2pay_ideal", indx + 1] = self.coupon.sprt_prcp_perCollect[indx]
            self.schedule_DF.at["sprt_intr_2pay_ideal", indx + 1] = self.coupon.sprt_intr_perCollect[indx]
            self.schedule_DF.at["corp_pnlt_2pay_ideal", indx] = self.coupon.corp_pnlt_perCollect[indx - 1]
            self.schedule_DF.at["sprt_pnlt_2pay_ideal", indx] = self.coupon.sprt_pnlt_perCollect[indx - 1]
            self.schedule_DF.at["brw_2pay_ideal", indx + 1] = self.coupon.corp_collect_current \
                                                              + self.coupon.sprt_collect_current
            self.schedule_DF.at["brw_2pay_finish", indx + 1] = self.coupon.corp_collect_full_repay \
                                                               + self.coupon.sprt_collect_full_repay
            
    def _next_allocations_from_coupon(self, indx, df, update_next_prd=True):
        """
        the newly updated coupon also gives us information on what are the amounts due in the next period
        the allocation dataframe is updated with these new amount for the next loan period

        Parameters
        ----------
        indx (int): period of loan
        df (dataframe): allocation dataframe

        Returns
        -------
        updated allocate_DF
        """

        # we need to adjust--moving some amounts into interest vs principal
        # because for borrowers interest is paid first vs principal
        # vise versa for lenders -- that is why a difference in principal oustanding for borrowers vs lenders
        corp_prcp_adjust_coef = min(1, 
            self.schedule_DF.at["corp_prcp_outstand_4corp", indx] / self.schedule_DF.at["corp_prcp_outstand_4brw", indx]
        )
        sprt_prcp_adjust_coef = min(1, 
            self.schedule_DF.at["sprt_prcp_outstand_4sprt", indx] / self.schedule_DF.at["sprt_prcp_outstand_4brw", indx]
        )

        df_indx = indx + update_next_prd
        df.at["corp_prcp_current", (df_indx, "owed")] = self.coupon.corp_prcp_perCollect[indx] * corp_prcp_adjust_coef
        df.at["sprt_prcp_current", (df_indx, "owed")] = self.coupon.sprt_prcp_perCollect[indx] * sprt_prcp_adjust_coef

        df.at["corp_intr_current", (df_indx, "owed")] = self.coupon.corp_intr_perCollect[
            indx
        ] + self.coupon.corp_prcp_perCollect[indx] * (1 - corp_prcp_adjust_coef)
        df.at["sprt_intr_current", (df_indx, "owed")] = self.coupon.sprt_intr_perCollect[
            indx
        ] + self.coupon.sprt_prcp_perCollect[indx] * (1 - sprt_prcp_adjust_coef)

        # principal can never exceed loan_amt
        diff_corp_prcp = df.loc["corp_prcp_current", pd.IndexSlice[:, "owed"]].sum() - self.loan_amt * (
            1 - self.sprt_shr
        )
        diff_sprt_prcp = df.loc["sprt_prcp_current", pd.IndexSlice[:, "owed"]].sum() - self.loan_amt * (self.sprt_shr)

        if diff_corp_prcp > 0:
            df.at["corp_prcp_current", (indx, "owed")] += -diff_corp_prcp
            df.at["corp_intr_current", (indx, "owed")] += diff_corp_prcp
        if diff_sprt_prcp > 0:
            df.at["sprt_prcp_current", (indx, "owed")] += -diff_sprt_prcp
            df.at["sprt_intr_current", (indx, "owed")] += diff_sprt_prcp

        return df

    def _breakdown_sprt_pmnt_sent2corp_i(self, indx, sprt_pmnt_sent2corp_i):
        """
        supporter payments are withheld for a period defined by sprt_lag
        they are used as collateral for the corpus when there is a payment shortfall
        in the advent that happens we need to break down what amount of the payment in escrow that is
        used to cover the shortfall was interest vs principal paid by the borrower to the supporter
        
        Parameters
        ----------
        indx (int): period of loan
        sprt_pmnt_sent2corp_i (float): amount sent to corpus to cover shortfall
        """

        # helper function that defines amount filled and amount remaining
        def fill_helper(amt_2_fill, amt_on_hand):
            amt_filled = min(amt_2_fill, amt_on_hand)
            new_amt_on_hand = amt_on_hand - amt_filled
            return amt_filled, new_amt_on_hand

        sprt_prcp = 0
        sprt_intr = 0
        if sprt_pmnt_sent2corp_i > 0:

            # total principal and interest being witheld
            tot_sprt_prcp_withheld = self.schedule_DF.loc["sprt_prcp_paid_actual", (indx - self.sprt_lag) : (indx - 1)].sum()
            tot_sprt_intr_withheld = self.schedule_DF.loc["sprt_intr_paid_actual", (indx - self.sprt_lag) : (indx - 1)].sum()

            sprt_intr, remainder = fill_helper(tot_sprt_intr_withheld, sprt_pmnt_sent2corp_i)
            sprt_prcp, remainder = fill_helper(tot_sprt_prcp_withheld, remainder)

        return sprt_prcp, sprt_intr

    def _update_schedule_from_allocations(self, indx, df, sprt_pmnt_sent2corp, finalize=False):
        """
        once the allocate_DF has been updated by the coupon we need to use that info to update the schedule

        Parameters
        ----------
        indx (int): period of loan
        df (dataframe): allocation datarame
        sprt_pmnt_sent2corp (float): any supporter repayments held in escrow and sent to corpus to cover downfall for the period
        """


        # encumbered cash that's been used
        cash_encumb_brw_from_sprt = (
            df.loc["sprt_cash_owed_curr", pd.IndexSlice[1:indx, "owed"]].to_numpy()
            - df.loc["sprt_cash_owed_curr", pd.IndexSlice[1:indx, "filled"]].to_numpy()
        )

        # encumbered portfolio that's been used
        ptfl_encumb_brw_from_sprt = (
            df.loc["sprt_ptfl_owed_curr", pd.IndexSlice[1:indx, "owed"]].to_numpy()
            - df.loc["sprt_ptfl_owed_curr", pd.IndexSlice[1:indx, "filled"]].to_numpy()
        )

        # amount to pay to supporter
        sprt_2pay_now = df.at["sprt_pmnt_backlog", (indx, "filled")]

        # amount to withhold from supporter
        sprt_pay_withheld = df.loc[["sprt_prcp_current", "sprt_intr_current"], (indx, "filled")].sum()

        # corpus to pay now
        corp_paid_actual = df.loc[["corp_prcp_current", "corp_intr_current"], (indx, "filled")].sum()

        # corpus principal
        corp_prcp_paid_actual = df.at["corp_prcp_current", (indx, "filled")]

        # corpus interest
        corp_intr_paid_actual = df.at["corp_intr_current", (indx, "filled")]

        # breakdown sprt_pmnt_sent2corp
        sprt_prcp_sent2corp_i, sprt_intr_sent2corp_i = \
            self._breakdown_sprt_pmnt_sent2corp_i(indx, sprt_pmnt_sent2corp[indx - 1])

        # supporter principal
        sprt_prcp_paid_actual = (
            df.at["sprt_prcp_current", (indx, "filled")]
            - cash_encumb_brw_from_sprt[indx - 1]
            - ptfl_encumb_brw_from_sprt[indx - 1]
            - sprt_prcp_sent2corp_i
        )  # sprt_pmnt_sent2corp[indx-1]
        # [indx-1] is because of numpy vs pandas indexing

        # supporter interest
        sprt_intr_paid_actual = df.at["sprt_intr_current", (indx, "filled")] - sprt_intr_sent2corp_i

        if finalize:
            self.schedule_DF.at["sprt_2pay_now", indx - 1] += sprt_2pay_now + sprt_pay_withheld
            self.schedule_DF.at["sprt_paid_withheld", indx - 1] = 0
            self.schedule_DF.at["corp_paid_actual", indx - 1] += corp_paid_actual
            self.schedule_DF.at["corp_prcp_paid_actual", indx - 1] += corp_prcp_paid_actual
            self.schedule_DF.at["corp_intr_paid_actual", indx - 1] += corp_intr_paid_actual
            self.schedule_DF.at["sprt_prcp_paid_actual", indx - 1] += sprt_prcp_paid_actual
            self.schedule_DF.at["sprt_intr_paid_actual", indx - 1] += sprt_intr_paid_actual
        else:
            self.schedule_DF.at["sprt_2pay_now", indx] = sprt_2pay_now
            self.schedule_DF.at["sprt_paid_withheld", indx] = sprt_pay_withheld
            self.schedule_DF.at["corp_paid_actual", indx] = corp_paid_actual
            self.schedule_DF.at["corp_prcp_paid_actual", indx] = corp_prcp_paid_actual
            self.schedule_DF.at["corp_intr_paid_actual", indx] = corp_intr_paid_actual
            self.schedule_DF.at["sprt_prcp_paid_actual", indx] = sprt_prcp_paid_actual
            self.schedule_DF.at["sprt_intr_paid_actual", indx] = sprt_intr_paid_actual

    def _calc_encumbrances_update_schedule(self, indx, df, finalize=False):
        """
        once the allocation dataframe is updated the encumbrances of the supporter and borrower collateral
        (all various collaterals for the corpus) must be updated in the schedule

        Parameters
        ----------
        indx (int): period of loan
        df (dataframe): allocation datarame
        """

        # helper function that defines amount filled and amount remaining
        def fill_helper(amt_2_fill, amt_on_hand):
            amt_filled = min(amt_2_fill, amt_on_hand)
            new_amt_on_hand = amt_on_hand - amt_filled
            return amt_filled, new_amt_on_hand

        # supporter cash and portfolio on-hand before unencumbrance
        sprt_ptfl_on_hand = df.loc[["sprt_ptfl_owed_bklg", "sprt_ptfl_owed_curr"], (indx, "filled")].sum()
        sprt_cash_on_hand = df.loc[["sprt_cash_owed_bklg", "sprt_cash_owed_curr"], (indx, "filled")].sum()

        # unencumbrance is treated a bit differently  (invoked with cash/ptfl on hand if all else filled)
        ## difference between owed and filled
        rows = list(df.index)
        delta = np.maximum(0, df.loc[rows[0:-4], (indx, "owed")] - df.loc[rows[0:-4], (indx, "filled")])

        ## compute unencumbrance amounts owed
        pct_prcp_filled = df.loc["corp_prcp_current", (indx, "filled")] / self.corp_prcp_outstand_init

        df.at["sprt_cash_unencumbr_curr", (indx, "owed")] = pct_prcp_filled * self.sprt_cash_encumbr
        df.at["sprt_ptfl_unencumbr_curr", (indx, "owed")] = pct_prcp_filled * self.sprt_ptfl_encumbr

        ## fill
        if np.round(delta.sum(), 1) == 0:
            df.at["sprt_cash_unencumbr_bklg", (indx, "filled")], sprt_cash_on_hand = fill_helper(
                df.loc["sprt_cash_unencumbr_bklg", (indx, "owed")], sprt_cash_on_hand
            )
            df.at["sprt_cash_unencumbr_curr", (indx, "filled")], sprt_cash_on_hand = fill_helper(
                df.loc["sprt_cash_unencumbr_curr", (indx, "owed")], sprt_cash_on_hand
            )
            df.at["sprt_ptfl_unencumbr_bklg", (indx, "filled")], sprt_ptfl_on_hand = fill_helper(
                df.loc["sprt_ptfl_unencumbr_bklg", (indx, "owed")], sprt_ptfl_on_hand
            )
            df.at["sprt_ptfl_unencumbr_curr", (indx, "filled")], sprt_ptfl_on_hand = fill_helper(
                df.loc["sprt_ptfl_unencumbr_curr", (indx, "owed")], sprt_ptfl_on_hand
            )

        # unencumbrances
        sprt_cash_unencumbr = df.loc[["sprt_cash_unencumbr_bklg", "sprt_cash_unencumbr_curr"], (indx, "filled")].sum()
        sprt_ptfl_unencumbr = df.loc[["sprt_ptfl_unencumbr_bklg", "sprt_ptfl_unencumbr_curr"], (indx, "filled")].sum()

        # backlog for next period = (backlog owed - backlog filled) + (current owed - current filled)
        delta = np.maximum(0, df.loc[:, (indx, "owed")] - df.loc[:, (indx, "filled")])

        if finalize:
            indx += -1

            self.schedule_DF.at["sprt_cash_unencumbr", indx] += sprt_cash_unencumbr
            self.schedule_DF.at["sprt_ptfl_unencumbr", indx] += sprt_ptfl_unencumbr

            # at last period release all encumbrances
            self.schedule_DF.at["sprt_cash_unencumbr", indx] += sprt_cash_on_hand
            self.schedule_DF.at["sprt_cash_remain", indx] = 0
            self.schedule_DF.at["sprt_ptfl_unencumbr", indx] += sprt_ptfl_on_hand
            self.schedule_DF.at["sprt_ptfl_remain", indx] = 0

            # update borrower collateral
            self.schedule_DF.at["brw_colt_send2corp", indx] = (
                self.corp_amt_paid_perPrd[indx + 1]
                - delta["sprt_cash_owed_curr"]
                - delta["sprt_ptfl_owed_curr"]
                - self.schedule_DF.at["sprt_pmnt_send2corp", indx]
            )
            self.schedule_DF.at["brw_colt_send2sprt", indx] = self.sprt_amt_paid_perPrd[indx + 1]
            self.schedule_DF.at["brw_colt_remain", indx] = df.at["brw_collateral_owed_curr", (indx + 1, "filled")]
            self.schedule_DF.at["brw_colt_used", indx] = (
                df.at["brw_collateral_owed_curr", (indx + 1, "owed")]
                - df.at["brw_collateral_owed_curr", (indx + 1, "filled")]
            )
        else:
            self.schedule_DF.at["sprt_cash_unencumbr", indx] = sprt_cash_unencumbr
            self.schedule_DF.at["sprt_cash_remain", indx] = sprt_cash_on_hand
            self.schedule_DF.at["sprt_ptfl_unencumbr", indx] = sprt_ptfl_unencumbr
            self.schedule_DF.at["sprt_ptfl_remain", indx] = sprt_ptfl_on_hand

            df.at["sprt_ptfl_owed_bklg", (indx + 1, "owed")] = (
                delta["sprt_ptfl_owed_bklg"] + delta["sprt_ptfl_owed_curr"]
            )
            df.at["sprt_cash_owed_bklg", (indx + 1, "owed")] = (
                delta["sprt_cash_owed_bklg"] + delta["sprt_cash_owed_curr"]
            )
            df.at["sprt_cash_unencumbr_bklg", (indx + 1, "owed")] = (
                delta["sprt_cash_unencumbr_bklg"] + delta["sprt_cash_unencumbr_curr"]
            )
            df.at["sprt_ptfl_unencumbr_bklg", (indx + 1, "owed")] = (
                delta["sprt_ptfl_unencumbr_bklg"] + delta["sprt_ptfl_unencumbr_curr"]
            )
            df.at["sprt_pmnt_backlog", (indx + 1, "owed")] += delta["sprt_pmnt_backlog"]

        # Update encumbrances in schedule_DF
        self.schedule_DF.at["sprt_cash_send2corp", indx] = delta["sprt_cash_owed_curr"]
        self.schedule_DF.at["sprt_cash_used", indx] = delta["sprt_cash_owed_bklg"] + delta["sprt_cash_owed_curr"]
        self.schedule_DF.at["sprt_cash_rtrn", indx] = delta["sprt_cash_owed_bklg"]

        self.schedule_DF.at["sprt_ptfl_send2corp", indx] = delta["sprt_ptfl_owed_curr"]
        self.schedule_DF.at["sprt_ptfl_used", indx] = delta["sprt_ptfl_owed_bklg"] + delta["sprt_ptfl_owed_curr"]
        self.schedule_DF.at["sprt_ptfl_rtrn", indx] = delta["sprt_ptfl_owed_bklg"]

        return df, sprt_cash_on_hand, sprt_ptfl_on_hand

    def calc_schedule(self, repayments=None, start_period: int = 1):
        """
        core logic: computes schedule as receivable funds cascade to different payables
        operating principal is the order in which the funds flow into different pools as described by variable indx

        Note: from the perspective of the borrower interest is paid first then principal, vise-versa from the perspective of the lender
              ergo now payments will flow to principal before interest

        Parameters
        ----------
        start_period (int): at what time period should we start calculations from

        Returns
        -------
        self.schedule_DF
        """

        # helper function that defines amount filled and amount remaining
        def fill_helper(amt_2_fill, amt_on_hand):
            amt_filled = min(amt_2_fill, amt_on_hand)
            new_amt_on_hand = amt_on_hand - amt_filled
            return amt_filled, new_amt_on_hand

        # the calc_schedule function should be invoked from self.update()
        if repayments is None:
            repayments = self.repayments
        if start_period == 1:
            if len(self.repayments) != self.prds_concld:
                repayments = copy.copy(self.repayments)
                self.repayments = self.prv_repayments
                self.update(repayments)
                return self
            elif bool(repayments):
                self.update(repayments)
                return self
            elif not bool(repayments) and self.prds_concld == 0:
                return self

        df = self.allocate_DF
        indx = list(df.index)
        # set schedule for next period
        self.schedule_DF.loc["brw_paid_actual", 1 : self.prds_concld] = self.repayments

        # retrieving state
        sprt_ptfl_on_hand = self.sprt_ptfl_on_hand[start_period - 1]  # encumbered portfolio available
        sprt_cash_on_hand = self.sprt_cash_on_hand[start_period - 1]  # encumbered cash available
        sprt_pmnt_on_hand = self.sprt_pmnt_on_hand[start_period - 1]  # payments owed to supporter but not released yet

        df.at["sprt_ptfl_owed_curr", (start_period, "owed")] = sprt_ptfl_on_hand
        df.at["sprt_cash_owed_curr", (start_period, "owed")] = sprt_cash_on_hand
        df.at["sprt_pmnt_backlog", (start_period, "owed")] = sprt_pmnt_on_hand

        finalize = False
        i = start_period
        while i <= (self.prds_concld + (self.prds_concld == self.loan_tnr)):
            # initially borrower pays payment
            if i < self.loan_tnr + 1:
                brw_pmnt = self.schedule_DF.at["brw_paid_actual", i]
                # if borrower repays in full
                if brw_pmnt >= self.schedule_DF.at["brw_2pay_finish", i] and self.loan_tnr >= i:
                    self.loan_tnr = i
                    self.brw_overpay = brw_pmnt
                    brw_pmnt = max(self.schedule_DF.at["brw_2pay_finish", i], self.schedule_DF.at["brw_2pay_ideal", i])
                    self.brw_overpay += -brw_pmnt
                j = i
            else:  # at end of loan borrower collateral comes into picture
                brw_pmnt = self.brw_collateral
                df.at["brw_collateral_owed_curr", (i, "owed")] = self.brw_collateral
                finalize = True
                j = i - 1

            # total assets on hand
            tot_assets_on_hand = sprt_ptfl_on_hand + sprt_cash_on_hand + sprt_pmnt_on_hand + brw_pmnt

            # tabulate amounts filled given the total cash on hand (fill happens in index order)
            for k in indx[0:-4]:
                df.at[k, (i, "filled")], tot_assets_on_hand = fill_helper(df.at[k, (i, "owed")], tot_assets_on_hand)

            # tabulate what happened to the retained supporter payment
            sprt_pmnt_used = (
                df.at["sprt_pmnt_backlog", pd.IndexSlice[i, "owed"]]
                - df.at["sprt_pmnt_backlog", pd.IndexSlice[i, "filled"]]
            )
            sprt_pmnt_rtrn = max(0, df.at["sprt_pmnt_backlog", pd.IndexSlice[i, "filled"]] - sprt_pmnt_on_hand)
            sprt_pmnt_send2corp_i = max(
                0,
                sprt_pmnt_used
                - (
                    self.schedule_DF.loc["sprt_pmnt_send2corp", 0 : (i - 1)].sum()
                    - self.schedule_DF.loc["sprt_pmnt_rtrn", 0 : (i - 1)].sum()
                    - sprt_pmnt_rtrn
                ),
            )
            # diff the vectors for send vs return
            sprt_pmnt_sent2corp = np.append(
                self.schedule_DF.loc["sprt_pmnt_send2corp", 1 : (i - 1)] - self.schedule_DF.loc["sprt_pmnt_rtrn", 1 : (i - 1)],
                sprt_pmnt_send2corp_i - sprt_pmnt_rtrn,
            )

            # encumbered cash that's been used
            cash_encumb_brw_from_sprt = (
                df.loc["sprt_cash_owed_curr", pd.IndexSlice[1:i, "owed"]].to_numpy()
                - df.loc["sprt_cash_owed_curr", pd.IndexSlice[1:i, "filled"]].to_numpy()
            )

            # encumbered portfolio that's been used
            ptfl_encumb_brw_from_sprt = (
                df.loc["sprt_ptfl_owed_curr", pd.IndexSlice[1:i, "owed"]].to_numpy()
                - df.loc["sprt_ptfl_owed_curr", pd.IndexSlice[1:i, "filled"]].to_numpy()
            )

            # amount paid to corpus per period
            corp_amt_paid_perPrd = df.loc[["corp_prcp_current", "corp_intr_current"], pd.IndexSlice[1:i, "filled"]].sum(
                axis=0
            )

            # amount paid to supporter per period
            sprt_amt_paid_perPrd = (
                df.loc[["sprt_prcp_current", "sprt_intr_current"], pd.IndexSlice[1:i, "filled"]].sum(axis=0)
                - cash_encumb_brw_from_sprt
                - ptfl_encumb_brw_from_sprt
                - sprt_pmnt_sent2corp
            )

            # include principal remaining
            prcp_remain_corp = self.coupon.corp_prcp_owed - df.at["corp_prcp_current", (i, "filled")]

            prcp_remain_sprt = self.coupon.sprt_prcp_owed - df.at["sprt_prcp_current", (i, "filled")]

            # distribute remaining assets to principal (indexing is weird cause prcp_remain is a pd series)
            if prcp_remain_corp > 0:
                corp_amt_paid_perPrd[i] += tot_assets_on_hand * prcp_remain_corp / (prcp_remain_corp + prcp_remain_sprt)
            if prcp_remain_sprt > 0:
                sprt_amt_paid_perPrd[i] += tot_assets_on_hand * prcp_remain_sprt / (prcp_remain_corp + prcp_remain_sprt)

            # remove the supporter payments that were sent to the corpus
            self.corp_amt_paid_perPrd = corp_amt_paid_perPrd
            self.sprt_amt_paid_perPrd = sprt_amt_paid_perPrd

            # we add the virtual payments from borrower collateral and the payment backlog to the prv prd
            if finalize:
                sprt_amt_paid_perPrd[-2] += sprt_amt_paid_perPrd[-1]
                corp_amt_paid_perPrd[-2] += corp_amt_paid_perPrd[-1]

            # update coupon
            self.coupon.update(corp_amt_paid_perPrd[0:j], sprt_amt_paid_perPrd[0:j])

            # if payment exceeded expected amount we need to redo allocations
            if tot_assets_on_hand > 10 ** (-DEFAULT_PRECISION_MONEY):

                # update allocations using new coupon
                df = self._next_allocations_from_coupon(i - 1, df)

                # total assets on hand
                tot_assets_on_hand = sprt_ptfl_on_hand + sprt_cash_on_hand + sprt_pmnt_on_hand + brw_pmnt

                # tabulate amounts filled given the total cash on hand (fill happens in index order)
                for k in indx[0:-4]:
                    df.at[k, (i, "filled")], tot_assets_on_hand = fill_helper(df.at[k, (i, "owed")], tot_assets_on_hand)

            # update schedule given new allocations
            self._update_schedule_from_allocations(i, df, sprt_pmnt_sent2corp, finalize)

            # update encumbrances
            df, sprt_cash_on_hand, sprt_ptfl_on_hand = self._calc_encumbrances_update_schedule(i, df, finalize)

            # update schedule from coupon
            self._update_schedule_from_coupon(i, finalize)

            # supporter payments on hand
            self.schedule_DF.at["sprt_pmnt_used", j] = sprt_pmnt_used
            self.schedule_DF.at["sprt_pmnt_rtrn", j] = sprt_pmnt_rtrn
            self.schedule_DF.at["sprt_pmnt_send2corp", j] = sprt_pmnt_send2corp_i
            self.schedule_DF.at["sprt_pmnt_remain", j] = max(
                0,
                sprt_pmnt_on_hand
                - self.schedule_DF.at["sprt_2pay_now", j]
                + self.schedule_DF.at["sprt_paid_withheld", j]
                - self.schedule_DF.at["sprt_pmnt_send2corp", j]
                + self.schedule_DF.at["sprt_pmnt_rtrn", j],
            )
            sprt_pmnt_on_hand = self.schedule_DF.at["sprt_pmnt_remain", j]  # schedule_DF.at["sprt_paid_withheld", i]
            # sprt_pmnt_2_recover = max(0,schedule_DF.at["sprt_pmnt_used",j] - sprt_pmnt_on_hand)

            if finalize:
                break

            # update allocation table
            df.at["sprt_pmnt_backlog", (min(self.loan_tnr + 1, (i + self.sprt_lag)), "owed")] += \
                self.schedule_DF.at["sprt_paid_withheld", i]
            df.at["sprt_cash_owed_curr", (i + 1, "owed")] = sprt_cash_on_hand
            df.at["sprt_ptfl_owed_curr", (i + 1, "owed")] = sprt_ptfl_on_hand

            # update allocations using new coupon
            df = self._next_allocations_from_coupon(i, df)

            # if i < self.loan_tnr:
            #    # Need to include back in supporter payments used to cover corpus
            #    schedule_DF.at["brw_2pay_ideal",  i + 1] += sprt_pmnt_2_recover
            #    schedule_DF.at["brw_2pay_finish", i + 1] += sprt_pmnt_2_recover
            # Save values
            self.sprt_ptfl_on_hand[i] = sprt_ptfl_on_hand  # encumbered portfolio available
            self.sprt_cash_on_hand[i] = sprt_cash_on_hand  # encumbered cash available
            self.sprt_pmnt_on_hand[i] = sprt_pmnt_on_hand

            # iterate counter
            i += 1

        # store state variables
        self.allocate_DF = df

        if self.prds_concld == self.loan_tnr:
            if self.schedule_DF.loc[["corp_prcp_outstand_4brw", "sprt_prcp_outstand_4brw"], self.prds_concld].sum() <= 0:
                self.pmnt_curr = 0
                self.full_single_repay = 0
            else:
                self.pmnt_curr = (
                    self.coupon.corp_collect_current + self.coupon.sprt_collect_current
                )  # + sprt_pmnt_2_recover
                self.full_single_repay = (
                    self.coupon.corp_collect_full_repay + self.coupon.sprt_collect_full_repay
                )  # + sprt_pmnt_2_recover
        else:
            self.pmnt_curr = self.schedule_DF.loc["brw_2pay_ideal", :].iloc[-1]
            self.full_single_repay = self.schedule_DF.loc["brw_2pay_finish", :].iloc[-1]

        # self._logger.info("Finished calling call_schedule")
        # self._logger.info(vars(self))

        return self

    def update(self, repayments: List[float] = []):
        """
        instead of reinitializing Loan object, object can be updated
        with new payments as they come in

        Parameters
        ----------
        repayments (List[float]): all previous repayments
        """

        # helper function
        def find_first_diff_in_vals(A, B):

            k = max(len(A), len(B))
            A = np.append(A, np.full(k - len(A), np.nan))
            B = np.append(B, np.full(k - len(B), np.nan))

            indx = np.where(np.equal(A, B) == False)[0]
            if indx.size > 0:
                indx = indx[0]
            else:
                indx = np.inf
            return indx

        # check at what index is there a difference
        indx_new = find_first_diff_in_vals(self.repayments, repayments)
        if indx_new < np.inf:

            # if we need to overwrite existing stuff
            if indx_new < self.prds_concld:
                # overwrite dataframes
                self.schedule_DF.iloc[8:, (indx_new + 1)] = np.nan
                self.schedule_DF.loc[:, (indx_new + 2) : max(indx_new + 2, self.prds_concld + 1)] = np.nan
                self.allocate_DF.loc[:, pd.IndexSlice[(indx_new + 1) :, :]] = 0

                # reinitialize allocation table
                self.allocate_DF.at["corp_prcp_current", ((indx_new + 1), "owed")] = \
                    self.schedule_DF.at["corp_prcp_2pay_ideal", (indx_new + 1)]
                self.allocate_DF.at["sprt_prcp_current", ((indx_new + 1), "owed")] = \
                    self.schedule_DF.at["sprt_prcp_2pay_ideal", (indx_new + 1)]
                self.allocate_DF.at["corp_intr_current", ((indx_new + 1), "owed")] = \
                    self.schedule_DF.at["corp_intr_2pay_ideal", (indx_new + 1)]
                self.allocate_DF.at["sprt_intr_current", ((indx_new + 1), "owed")] = \
                    self.schedule_DF.attrs["sprt_intr_2pay_ideal", (indx_new + 1)]

                # reinitialize coupon
                self._init_coupon(self.corp_amt_paid_perPrd[0:indx_new],self.sprt_amt_paid_perPrd[0:indx_new])

            # update
            self.repayments = np.append(self.repayments[0:indx_new], repayments[indx_new:]).tolist()
            self.prv_repayments = copy.copy(self.repayments)
            self.amt_repaid = np.sum(self.repayments)  # total amount repaid
            self.prds_concld = len(self.repayments)  # periods concluded
            self.prds_remain = self.loan_tnr - self.prds_concld  # periods remaining

            # add new coulmns to allocation table and schedule
            cols = np.arange(0, min(self.loan_tnr + 1, self.prds_concld + 2))
            self.schedule_DF = self.schedule_DF.reindex(columns=cols)
            cols = pd.MultiIndex.from_product([np.arange(1, self.prds_concld + 2), ["owed", "filled"]])
            self.allocate_DF = self.allocate_DF.reindex(columns=cols).fillna(0)

            # invoke main function
            self.calc_schedule(repayments=[], start_period=indx_new + 1)

    def _summarize_borrower_perspective(self):
        """
        summarizes schedule into amounts paid and remaining for the borrower with respect to 
        principal vs interest and supporter vs corpus

        Returns
        -------
        a dataframe
        """

        cols = ["paid", "remain"]

        # create dataframe
        rows = [
            "total_payments",
            "corpus_principal",
            "supporter_principal",
            "corpus_interest",
            "supporter_interest",
            "borrower_collateral",
        ]
        df = pd.DataFrame(np.full([len(rows), len(cols)], np.NaN), index=rows, columns=cols).astype("float64")

        # fill
        df.at["total_payments", "paid"] = np.nansum(self.repayments)
        df.at["total_payments", "remain"] = (
            self.coupon.corp_pmnt_perCollect[self.prds_concld :].sum()
            + self.coupon.sprt_pmnt_perCollect[self.prds_concld :].sum()
        )
        df.at["corpus_principal", "paid"] = self.coupon.corp_prcp_paid
        df.at["corpus_principal", "remain"] = self.coupon.corp_prcp_owed
        df.at["supporter_principal", "paid"] = self.coupon.sprt_prcp_paid
        df.at["supporter_principal", "remain"] = self.coupon.sprt_prcp_owed
        df.at["corpus_interest", "paid"] = self.coupon.corp_intr_paid \
                                           + np.where(self.coupon.corp_pnlt_perCollect[0:self.prds_concld]<0,0,
                                                      self.coupon.corp_pnlt_perCollect[0:self.prds_concld]).sum()
        df.at["corpus_interest", "remain"] = self.coupon.corp_intr_owed
        df.at["supporter_interest", "paid"] = self.coupon.sprt_intr_paid \
                                               + np.where(self.coupon.sprt_pnlt_perCollect[0:self.prds_concld]<0,0,
                                                          self.coupon.sprt_pnlt_perCollect[0:self.prds_concld]).sum()
        df.at["supporter_interest", "remain"] = self.coupon.sprt_intr_owed
        df.at["borrower_collateral", "paid"] = self.schedule_DF.at["brw_colt_used", self.prds_concld]
        df.at["borrower_collateral", "remain"] = self.schedule_DF.at["brw_colt_remain", self.prds_concld]

        return df

    def _summarize_supporter_perspective(self):
        """
        summarizes schedule into amounts paid and remaining for the supporter
        organized by principal vs interest, payments being held vs released, encumbrances being held vs released
        and collaterals (enucmbrances, past payments) that are confiscated and sent to the corpus

        Returns
        -------
        a dataframe
        """

        cols = ["paid", "remain"]

        # create dataframe
        rows = [
            "total_receipts",
            "supporter_principal",
            "supporter_interest",
            "receipts_in_escrow",
            "receipts_rtrn_from_brw",
            "cash_unencumbered",
            "cash_rtrn_from_brw",
            "ptfl_unencumbered",
            "ptfl_rtrn_from_brw",
            "total_released",
            "principal_released",
            "interest_released",
        ]
        df = pd.DataFrame(np.full([len(rows), len(cols)], np.NaN), index=rows, columns=cols).astype("float64")

        # receipts
        self.coupon.sprt_collect_current * (self.prds_concld < self.loan_tnr)
        df.at["total_receipts", "remain"] = self.coupon.sprt_pmnt_perCollect[self.prds_concld :].sum()
        df.at["total_receipts", "paid"] = (
            self.schedule_DF.loc[["sprt_intr_paid_actual", "sprt_prcp_paid_actual"], 1 : self.prds_concld].sum().sum()
        )

        df.at["supporter_principal", "paid"] = (
            self.sprt_prcp_outstand_init - self.schedule_DF.at["sprt_prcp_outstand_4sprt", self.prds_concld]
        )
        df.at["supporter_principal", "remain"] = self.schedule_DF.at["sprt_prcp_outstand_4sprt", self.prds_concld]

        df.at["supporter_interest", "paid"] = self.schedule_DF.loc["sprt_intr_paid_actual", 1 : self.prds_concld].sum()
        df.at["supporter_interest", "remain"] = self.schedule_DF.at["sprt_intr_outstand_4sprt", self.prds_concld]

        df.at["receipts_in_escrow", "paid"] = self.schedule_DF.loc["sprt_2pay_now", 1 : self.prds_concld].sum()
        df.at["receipts_in_escrow", "remain"] = self.schedule_DF.at["sprt_pmnt_remain", self.prds_concld]

        df.at["receipts_rtrn_from_brw", "paid"] = (
            self.schedule_DF.loc["sprt_pmnt_send2corp", 1 : self.prds_concld].sum()
            - self.schedule_DF.at["sprt_pmnt_used", self.prds_concld]
        )
        df.at["receipts_rtrn_from_brw", "remain"] = self.schedule_DF.loc["sprt_pmnt_used", self.prds_concld]
        df.at["cash_rtrn_from_brw", "paid"] = (
            self.schedule_DF.loc["sprt_cash_send2corp", 1 : self.prds_concld].sum()
            - self.schedule_DF.at["sprt_cash_used", self.prds_concld]
        )
        df.at["cash_rtrn_from_brw", "remain"] = self.schedule_DF.loc["sprt_cash_used", self.prds_concld]
        df.at["ptfl_rtrn_from_brw", "paid"] = (
            self.schedule_DF.loc["sprt_ptfl_send2corp", 1 : self.prds_concld].sum()
            - self.schedule_DF.at["sprt_ptfl_used", self.prds_concld]
        )
        df.at["ptfl_rtrn_from_brw", "remain"] = self.schedule_DF.loc["sprt_ptfl_used", self.prds_concld]

        df.at["cash_unencumbered", "paid"] = self.schedule_DF.loc["sprt_cash_unencumbr", 1 : self.prds_concld].sum()
        df.at["cash_unencumbered", "remain"] = self.schedule_DF.at["sprt_cash_remain", self.prds_concld]
        df.at["ptfl_unencumbered", "paid"] = self.schedule_DF.loc["sprt_ptfl_unencumbr", 1 : self.prds_concld].sum()
        df.at["ptfl_unencumbered", "remain"] = self.schedule_DF.at["sprt_ptfl_remain", self.prds_concld]

        df.at["total_released", "paid"] = df.at["receipts_in_escrow", "paid"]
        df.at["total_released", "remain"] = df.at["receipts_in_escrow", "remain"] + df.at["total_receipts", "remain"]

        sprt_prcp_unreleased, sprt_intr_unreleased = self._breakdown_sprt_pmnt_sent2corp_i(
            self.prds_concld + 1, df.at["receipts_in_escrow", "remain"]
        )

        df.at["principal_released", "paid"] = df.at["supporter_principal", "paid"] - sprt_prcp_unreleased
        df.at["principal_released", "remain"] = df.at["supporter_principal", "remain"] + sprt_prcp_unreleased
        df.at["interest_released", "paid"] = df.at["supporter_interest", "paid"] - sprt_intr_unreleased
        df.at["interest_released", "remain"] = df.at["supporter_interest", "remain"] + sprt_intr_unreleased

        return df

    def _summarize_corpus_perspective(self):
        """
        summarizes corpus into amounts paid and remaining for the corpus
        organized by principal vs interest

        Returns
        -------
        a dataframe
        """

        cols = ["paid", "remain"]

        # create dataframe
        rows = ["total_receipts", "principal", "interest"]
        df = pd.DataFrame(np.full([len(rows), len(cols)], np.NaN), index=rows, columns=cols).astype("float64")

        # receipts
        self.coupon.corp_collect_current * (self.prds_concld < self.loan_tnr)
        df.at["total_receipts", "remain"] = np.nansum(self.coupon.corp_pmnt_perCollect[self.prds_concld :])

        # fill
        df.at["total_receipts", "paid"] = (
            self.schedule_DF.loc[["corp_intr_paid_actual", "corp_prcp_paid_actual"], 1 : self.prds_concld].sum().sum()
        )
        df.at["principal", "paid"] = (
            self.corp_prcp_outstand_init - self.schedule_DF.at["corp_prcp_outstand_4corp", self.prds_concld]
        )
        df.at["principal", "remain"] = self.schedule_DF.at["corp_prcp_outstand_4corp", self.prds_concld]
        df.at["interest", "paid"] = self.schedule_DF.loc["corp_intr_paid_actual", 1 : self.prds_concld].sum()
        df.at["interest", "remain"] = self.schedule_DF.at["corp_intr_outstand_4corp", self.prds_concld]

        return df

    def summarize_schedule(self, perspective="borrower"):
        """
        summarizes fields in schedule_df into a dataframe with two columns (paid,remain)
        and various rows relevant to the perspective

        Parameters
        ----------
        perspective (str): either 'borrower','corpus','supporter'

        Returns
        -------
        if borrower: summary_dataframe , next_period_payment
        if corpus: summary_dataframe , next_period_receipt, IRR
        if supporter: summary_dataframe , next_period_receipt, IRR
        """

        if perspective == "borrower":

            df = self._summarize_borrower_perspective().fillna(0)

            if self.pmnt_curr != self.pmnt_curr:
                raise InternalError("Critical error: next payment can not be NaN")

            # self._logger.info("Finished calling summarize_schedule from the perspective of the %s", perspective)
            return df, self.pmnt_curr

        elif perspective == "corpus":

            df = self._summarize_corpus_perspective().fillna(0)
            receipt = self.coupon.corp_collect_current * (self.prds_concld < self.loan_tnr)
            # self._logger.info("Finished calling summarize_schedule from the perspective of the %s", perspective)
            return df, receipt, self.schedule_DF.loc["corp_IRR", self.prds_concld]

        elif perspective == "supporter":

            df = self._summarize_supporter_perspective().fillna(0)
            receipt = self.coupon.sprt_collect_current * (self.prds_concld < self.loan_tnr)
            # self._logger.info("Finished calling summarize_schedule from the perspective of the %s", perspective)
            # self._logger.info(vars(self))
            return df, receipt, self.schedule_DF.loc["sprt_IRR", self.prds_concld]

    def summary(self):
        # get apr for corpus & supporter
        schedule, next_payment = self.summarize_schedule()
        return LoanScheduleSummary(
            request_id=self.id,
            borrower_view=schedule.to_dict(orient="index"),
            supporter_view=self.summarize_schedule(perspective="supporter")[0].to_dict(orient="index"),
            corpus_view=self.summarize_schedule(perspective="corpus")[0].to_dict(orient="index"),
            next_borrower_payment=np.round(next_payment, DEFAULT_PRECISION_MATH_OPERATIONS),
            apr=self.get_aprs(),
            full_single_repay=self.full_single_repay,
        )

    def get_aprs(self):
        corpus_irr = self.schedule_DF.loc["corp_IRR", len(self.repayments)]
        supporter_irr = self.schedule_DF.loc["sprt_IRR", len(self.repayments)]
        if ~np.isnan(supporter_irr) and supporter_irr > -1:
            supporter_apr = LoanMath.calc_APR_NPV(self.loan_amt, self.loan_tnr, supporter_irr)[0]
        else:
            supporter_apr = -np.inf
        if ~np.isnan(corpus_irr) and corpus_irr > -1:
            corpus_apr = LoanMath.calc_APR_NPV(self.loan_amt, self.loan_tnr, corpus_irr)[0]
        else:
            corpus_irr = -np.inf

        return APR(corpus=corpus_apr, supporter=supporter_apr)
     
    def fetch_repayment_amount(self,repayment_date, full_repay = False):
        """
        returns the repayment amount for a period and total amount to repay to settle loan

        Parameters
        ----------
        repayment_date (dt.datetime or int): can be either an integer for the period or the date if loan parameterized with repayment dates
        full_repay (bool): return full_repayment amount or solely amount due this period

        Returns
        -------
        tuple by corpus, supporter 
        """
        # get the repayment amount given date of period
        return self.coupon.fetch_repayment_amount(repayment_date, full_repay)

    @property
    def fully_repaid(self):
        # TODO
        # self.coupon.corp_prcp_owed == self.coupon.sprt_prcp_owed < Fraction_amount
        # return self.summary().borrower_view.total_payments.remain < .01
        return (self.full_single_repay / self.loan_amt) < 0.0001

    @property
    def escrow(self):
        return self.schedule_DF.loc["sprt_pmnt_remain", self.prds_concld]

    @property
    def status(self):
        if self.fully_repaid:
            return 'settled'
        elif not self.fully_repaid and self.prds_concld == self.loan_tnr:
            return 'defaulted'
        elif self.prds_concld > 0 and \
             (self.schedule_DF.at["brw_2pay_ideal", self.prds_concld] \
              - self.schedule_DF.at["brw_paid_actual", self.prds_concld]) > DEFAULT_PRECISION_MONEY:
            return 'underpaid'
        else:
            return 'live'

    def get_payment_breakdown(self, period=None):
        if not period:
            period = self.prds_concld
        return RepaymentBreakdown(
            influx=self.repayments[period - 1],
            to_corpus=PaymentSplit(
                principal=self.schedule_DF.loc["corp_prcp_paid_actual", period],
                interest=self.schedule_DF.loc["corp_intr_paid_actual", period],
            ),
            to_supporter=self.schedule_DF.loc["sprt_2pay_now", period],
            to_escrow=self.schedule_DF.loc["sprt_paid_withheld", period],
        )
