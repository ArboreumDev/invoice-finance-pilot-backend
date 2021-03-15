from typing import Any, List

import numpy as np

from common.constant import DEFAULT_PRECISION_MONEY
from loan.coupon import Coupon


class Disbursal:
    def __init__(
        self,
        prcp_corp: List[float],
        prcp_sprt: List[float],
        APR_corp: float,
        APR_sprt: float,
        loan_tnr: float,
        pct_balloon: float = np.nan,
        pct_min_pmnt: float = np.nan,
        prv_pmnts_corp: List[float] = [],
        prv_pmnts_sprt: List[float] = [],
        subsprt_info: Any = {},
        APR_pnlt: float = 0,
        max_slope: float = np.inf,
        annual_cmpnd_prds: int = 360,
        collection_freq: int = 15,
        sig_figs_2rnd: int = DEFAULT_PRECISION_MONEY,
        tol: float = 10 ** (-DEFAULT_PRECISION_MONEY - 1),
        num_CPUs=1,
    ):

        """
        stub for how credit-line coupon calc will work
        need variables for
        (1) max amount of credit line (can be same as loan amount)
        (2) dibursals per period
        (3) minimum payment per month -- ideally we want a variable equivocating this to time
        (4) for a given dibursal -- when must that be repaid (same as loan_tnr)
        (5) perhaps the supporter share or we can do separate vectors for supporter and corpus disbursals

        each dibursal is thus effectively treated as its own loan with some minimum payment in the interim periods
        and an additional lump-sum at the final period. repayments are applied in order of oldest to newest loan.
        the whole thing can then simply be added up
        """

        # basic assertion
        assert len(prv_pmnts_corp) == len(prv_pmnts_sprt), "payments of different length for corpus vs supporters"

        self.prv_pmnts_corp = []
        self.prv_pmnts_sprt = []
        self.num_prv_pmnts = 0

        # attribute to store
        self.prcp_corp_init = prcp_corp
        self.prcp_sprt_init = prcp_sprt

        self.loan_tnr = loan_tnr
        self.pct_min_pmnt = pct_min_pmnt
        self.pct_balloon = pct_balloon

        # attributes we only need for initialization and can forget about
        init_attr = {
            "APR_corp": APR_corp,
            "APR_sprt": APR_sprt,
            "APR_pnlt": APR_pnlt,
            "sig_figs_2rnd": sig_figs_2rnd,
            "tol": tol,
            "max_slope": max_slope * (loan_tnr > 1),
            "num_CPUs": num_CPUs,
            "annual_cmpnd_prds": annual_cmpnd_prds,
            "collection_freq": collection_freq,
            "subsprt_info": subsprt_info,
        }

        # min payment converted to time
        if not np.isnan(self.pct_min_pmnt):
            self.pct_prcp_annuity = self._convert_pct_min_pmnt_2_annuity_prcp(init_attr)
        elif not np.isnan(self.pct_balloon):
            self.pct_prcp_annuity = self._convert_pct_balloon_2_annuity_prcp(init_attr)

        self.prcp_corp_annuity = self.prcp_corp_init * self.pct_prcp_annuity
        self.prcp_sprt_annuity = self.prcp_sprt_init * self.pct_prcp_annuity
        self.prcp_corp_balloon = self.prcp_corp_init * (1 - self.pct_prcp_annuity)
        self.prcp_sprt_balloon = self.prcp_sprt_init * (1 - self.pct_prcp_annuity)

        # initial coupons
        self._calc_init_coupons(init_attr)

        # update if repayments
        if len(prv_pmnts_corp) > 0:
            self.update(prv_pmnts_corp, prv_pmnts_sprt)

    def _convert_pct_balloon_2_annuity_prcp(self, init_attr):

        # pct of principal to be covered by first loan_tnr-1 periods
        prcp_covered_annuity = (1 - self.pct_balloon) * (self.prcp_corp_init + self.prcp_sprt_init)

        # being lazy and brute-force solving it
        def function_2_solve(pct_prcp_annuity):
            coupon = Coupon(
                prcp_corp=self.prcp_corp_init * pct_prcp_annuity[0],
                prcp_sprt=self.prcp_sprt_init * pct_prcp_annuity[0],
                APR_corp=init_attr["APR_corp"],
                APR_sprt=init_attr["APR_sprt"],
                loan_tnr=self.loan_tnr,
                prv_pmnts_corp=[],
                prv_pmnts_sprt=[],
                subsprt_info=init_attr["subsprt_info"],
                APR_pnlt=init_attr["APR_pnlt"],
                max_slope=0,  # init_attr['max_slope'],
                annual_cmpnd_prds=init_attr["annual_cmpnd_prds"],
                collection_freq=init_attr["collection_freq"],
                sig_figs_2rnd=init_attr["sig_figs_2rnd"],
                tol=init_attr["tol"],
                num_CPUs=init_attr["num_CPUs"],
            )

            prcp_covered_hat = coupon.corp_prcp_perCollect[0:-1].sum() + coupon.sprt_prcp_perCollect[0:-1].sum()
            return prcp_covered_hat - prcp_covered_annuity

        # Find Roots
        pct_prcp_annuity = optimize.fsolve(function_2_solve, (1 - self.pct_balloon))

        return pct_prcp_annuity[0]

    def _convert_pct_min_pmnt_2_annuity_prcp(self, init_attr):

        # convert to actual amount paid
        min_pmnt = self.pct_min_pmnt * (self.prcp_corp_init + self.prcp_sprt_init)

        # being lazy and brute-force solving it
        def function_2_solve(pct_prcp_annuity):
            coupon = Coupon(
                prcp_corp=self.prcp_corp_init * pct_prcp_annuity[0],
                prcp_sprt=self.prcp_sprt_init * pct_prcp_annuity[0],
                APR_corp=init_attr["APR_corp"],
                APR_sprt=init_attr["APR_sprt"],
                loan_tnr=self.loan_tnr,
                prv_pmnts_corp=[],
                prv_pmnts_sprt=[],
                subsprt_info=init_attr["subsprt_info"],
                APR_pnlt=init_attr["APR_pnlt"],
                max_slope=0,  # init_attr['max_slope'],
                annual_cmpnd_prds=init_attr["annual_cmpnd_prds"],
                collection_freq=init_attr["collection_freq"],
                sig_figs_2rnd=init_attr["sig_figs_2rnd"],
                tol=init_attr["tol"],
                num_CPUs=init_attr["num_CPUs"],
            )

            pmnt_hat = coupon.corp_prcp_perCollect[1] + coupon.sprt_prcp_perCollect[1]
            return pmnt_hat - min_pmnt

        # Find Roots
        init_guess = (self.prcp_corp_init + self.prcp_sprt_init) / min_pmnt
        pct_prcp_annuity = optimize.fsolve(function_2_solve, init_guess)

        return pct_prcp_annuity[0]

    def _calc_init_coupons(self, init_attr):

        # calc annuity coupon for single disbursal
        coupon_annuity = Coupon(
            prcp_corp=self.prcp_corp_annuity,
            prcp_sprt=self.prcp_sprt_annuity,
            APR_corp=init_attr["APR_corp"],
            APR_sprt=init_attr["APR_sprt"],
            loan_tnr=self.loan_tnr,
            prv_pmnts_corp=[],
            prv_pmnts_sprt=[],
            subsprt_info=init_attr["subsprt_info"],
            APR_pnlt=init_attr["APR_pnlt"],
            max_slope=init_attr["max_slope"],
            annual_cmpnd_prds=init_attr["annual_cmpnd_prds"],
            collection_freq=init_attr["collection_freq"],
            sig_figs_2rnd=init_attr["sig_figs_2rnd"],
            tol=init_attr["tol"],
            num_CPUs=init_attr["num_CPUs"],
        )

        # calc balloon payment coupon for single disbursal
        corp_pmnts_annuity = coupon_annuity.corp_pmnt_perCollect[0:-1]
        sprt_pmnts_annuity = coupon_annuity.sprt_pmnt_perCollect[0:-1]

        coupon_balloon = Coupon(
            prcp_corp=self.prcp_corp_init,
            prcp_sprt=self.prcp_sprt_init,
            APR_corp=init_attr["APR_corp"],
            APR_sprt=init_attr["APR_sprt"],
            loan_tnr=self.loan_tnr,
            prv_pmnts_corp=corp_pmnts_annuity,
            prv_pmnts_sprt=sprt_pmnts_annuity,
            subsprt_info=init_attr["subsprt_info"],
            APR_pnlt=0,
            max_slope=0,
            annual_cmpnd_prds=init_attr["annual_cmpnd_prds"],
            collection_freq=init_attr["collection_freq"],
            sig_figs_2rnd=init_attr["sig_figs_2rnd"],
            tol=init_attr["tol"],
            num_CPUs=init_attr["num_CPUs"],
        )

        # store
        self.coupon_annuity = coupon_annuity
        self.coupon_balloon = coupon_balloon
        self._coalesce()

        # store ideal payments
        self.ideal_corp_pmnts_init = coupon_balloon.corp_pmnt_perCollect.copy()
        self.ideal_sprt_pmnts_init = coupon_balloon.sprt_pmnt_perCollect.copy()

    def _coalesce(self):

        # combine outputs of coupons together
        self.corp_pmnt_perCollect = self.coupon_balloon.corp_pmnt_perCollect
        self.corp_prcp_perCollect = self.coupon_balloon.corp_prcp_perCollect
        self.corp_intr_perCollect = self.coupon_balloon.corp_intr_perCollect
        self.corp_pnlt_perCollect = np.append(
            self.coupon_annuity.corp_pnlt_perCollect[0:-1],
            self.coupon_balloon.corp_pnlt_perCollect[(self.loan_tnr - 1) :],
        )

        self.corp_collect_current = self.corp_pmnts[self.num_prv_pmnts]
        self.corp_intr_owed = self.corp_intr_perCollect[self.num_prv_pmnts :].sum()
        self.corp_prcp_paid = self.corp_prcp_perCollect[0 : self.num_prv_pmnts].sum()
        self.corp_intr_paid = self.corp_intr_perCollect[0 : self.num_prv_pmnts].sum()
        self.corp_prcp_owed = self.prcp_corp_init - self.corp_prcp_paid
        self.corp_collect_full_repay = self.corp_intr_perCollect[self.num_prv_pmnts] + self.corp_prcp_owed

        self.sprt_pmnt_perCollect = self.coupon_balloon.sprt_pmnt_perCollect
        self.sprt_prcp_perCollect = self.coupon_balloon.sprt_prcp_perCollect
        self.sprt_intr_perCollect = self.coupon_balloon.sprt_intr_perCollect
        self.sprt_pnlt_perCollect = np.append(
            self.coupon_annuity.sprt_pnlt_perCollect[0:-1],
            self.coupon_balloon.sprt_pnlt_perCollect[(self.loan_tnr - 1) :],
        )

        self.sprt_collect_current = self.sprt_pmnts[self.num_prv_pmnts]
        self.sprt_intr_owed = self.sprt_intr_perCollect[self.num_prv_pmnts :].sum()
        self.sprt_prcp_paid = self.sprt_prcp_perCollect[0 : self.num_prv_pmnts].sum()
        self.sprt_intr_paid = self.sprt_intr_perCollect[0 : self.num_prv_pmnts].sum()
        self.sprt_prcp_owed = self.prcp_sprt_init - self.sprt_prcp_paid
        self.sprt_collect_full_repay = self.sprt_intr_perCollect[self.num_prv_pmnts] + self.corp_prcp_owed

    def update(self, prv_pmnts_corp: List[float] = [], prv_pmnts_sprt: List[float] = []):

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

        # assert prv_pmnts len is same
        assert len(prv_pmnts_corp) == len(prv_pmnts_corp), "previous payment vectors of different lengths"

        # check at what index is there a difference
        indx_diff_corp = find_first_diff_in_vals(self.prv_pmnts_corp, prv_pmnts_corp)
        indx_diff_sprt = find_first_diff_in_vals(self.prv_pmnts_sprt, prv_pmnts_sprt)
        indx_new = min(indx_diff_corp, indx_diff_sprt)

        if indx_new < np.inf:
            # update vectors
            self.prv_pmnts_corp = np.append(self.prv_pmnts_corp[0:indx_new], prv_pmnts_corp[indx_new:])
            self.prv_pmnts_sprt = np.append(self.prv_pmnts_sprt[0:indx_new], prv_pmnts_sprt[indx_new:])
            self.num_prv_pmnts = len(self.prv_pmnts_corp)

            # update annuity coupon
            self.coupon_annuity.update(prv_collect_corp=self.prv_pmnts_corp, prv_collect_sprt=self.prv_pmnts_sprt)

            # extract payments - penalties
            corp_pmnts_annuity = self.coupon_annuity.corp_pmnt_perCollect[0:-1] - np.where(
                self.coupon_annuity.corp_pnlt_perCollect[0:-1] < 0, 0, self.coupon_annuity.corp_pnlt_perCollect[0:-1]
            )
            sprt_pmnts_annuity = self.coupon_annuity.sprt_pmnt_perCollect[0:-1] - np.where(
                self.coupon_annuity.sprt_pnlt_perCollect[0:-1] < 0, 0, self.coupon_annuity.sprt_pnlt_perCollect[0:-1]
            )

            # update balloon coupon
            self.coupon_balloon.update(prv_collect_corp=corp_pmnts_annuity, prv_collect_sprt=sprt_pmnts_annuity)
            # update internal values
            self._coalesce()

    def to_dict(self, by_collections=True):
        # outputs essential coupon attributes as a dict
        return {
            "corp_pmnts": self.corp_pmnts,
            "corp_pmnt_current": self.corp_pmnt_current,
            "corp_prcp_perPrd": self.corp_prcp_perPrd,
            "corp_intr_perPrd": self.corp_intr_perPrd,
            "corp_pnlt_perPrd": self.corp_pnlt_perPrd,
            "sprt_pmnts": self.sprt_pmnts,
            "sprt_pmnt_current": self.sprt_pmnt_current,
            "sprt_prcp_perPrd": self.sprt_prcp_perPrd,
            "sprt_intr_perPrd": self.sprt_intr_perPrd,
            "sprt_pnlt_perPrd": self.sprt_pnlt_perPrd,
        }


class CreditLine:
    def __init__(
        self,
        APR_corp: float,
        APR_sprt: float,
        loan_tnr: float,
        max_credit_line: float,
        pct_min_pmnt: float = np.nan,
        pct_balloon: float = np.nan,
        disbursals_corp: List[float] = [],
        disbursals_sprt: List[float] = [],
        repayments_corp: List[float] = [],
        repayments_sprt: List[float] = [],
        subsprt_info: Any = {},
        APR_pnlt: float = 0,
        max_slope: float = np.inf,
        annual_cmpnd_prds: int = 360,
        collection_freq: int = 15,
        sig_figs_2rnd: int = DEFAULT_PRECISION_MONEY,
        tol: float = 10 ** (-DEFAULT_PRECISION_MONEY - 1),
        num_CPUs=1,
    ):

        return True
