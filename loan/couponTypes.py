from typing import Any, List, Tuple, Dict
import numpy as np
import datetime as dt

from collections import defaultdict, namedtuple, Counter, OrderedDict
from numpy.core.fromnumeric import nonzero
from pydantic.types import NoneStrBytes
from scipy import optimize

from loan.LoanMath import LoanMath
from loan.coupon import Coupon
from common.constant import (DEFAULT_DISCOUNT_APR,
                                     DEFAULT_PRECISION_MATH_OPERATIONS,
                                     DEFAULT_PRECISION_MONEY,
                                     DEFAULT_SUPPORTER_LAG)


def generate_coupon(
    prcp_corp: float,
    prcp_sprt: float,
    APR_corp: float,
    APR_sprt: float,
    loan_tnr: float,
    collection_freq: int,
    annual_cmpnd_prds: int,
    balloon_params: Any=None,
    prv_pmnts_corp: List[float]=[],
    prv_pmnts_sprt: List[float]=[],
    subsprt_info: Any={},
    APR_pnlt: float=0,
    max_slope: float=np.inf,
    collection_dates: List[dt.datetime] = [],
    sig_figs_2rnd: int = DEFAULT_PRECISION_MONEY,
    tol: float = 10**(-DEFAULT_PRECISION_MONEY-1),
    num_CPUs = 1,
    coupon_type = 'standard'):
    """
    this function is meant to be the universal coupon generator in the system for all coupon types
    there is in fact only one "base coupon" type but other coupons can be built by combining multiple coupons

    Returns
    -------
    coupon object of appropriate type
    """


    # initialize coupon (core math logic here)  
    if balloon_params:

        return BalloonCoupon(
                    prcp_corp=prcp_corp,
                    prcp_sprt=prcp_sprt,
                    APR_corp=APR_corp,
                    APR_sprt=APR_sprt,
                    loan_tnr=loan_tnr,
                    balloon_params = balloon_params,
                    collection_freq=collection_freq,
                    annual_cmpnd_prds=annual_cmpnd_prds,
                    prv_pmnts_corp=prv_pmnts_corp,
                    prv_pmnts_sprt=prv_pmnts_sprt,
                    subsprt_info=subsprt_info,
                    APR_pnlt=APR_pnlt,
                    max_slope=max_slope,
                    collection_dates=collection_dates,
                    sig_figs_2rnd=sig_figs_2rnd,
                    tol=tol,
                    num_CPUs=num_CPUs)
    else:
        return Coupon(
                    prcp_corp=prcp_corp,
                    prcp_sprt=prcp_sprt,
                    APR_corp=APR_corp,
                    APR_sprt=APR_sprt,
                    loan_tnr=loan_tnr,
                    collection_freq=collection_freq,
                    annual_cmpnd_prds=annual_cmpnd_prds,
                    prv_pmnts_corp=prv_pmnts_corp,
                    prv_pmnts_sprt=prv_pmnts_sprt,
                    subsprt_info=subsprt_info,
                    APR_pnlt=APR_pnlt,
                    max_slope=max_slope,
                    collection_dates=collection_dates,
                    sig_figs_2rnd=sig_figs_2rnd,
                    tol=tol,
                    num_CPUs=num_CPUs)

class BalloonCoupon:

    __slots__ = ['coupon_annuity',
                 'coupon_balloon',
                 'collection_dict',
                 'repayment_dict',
                 'tenor_annuity',
                 'fst_pmnt_pct_annuity',
                 'pct_prcp_annuity',
                 'loan_tnr',
                 'ideal_pmnts_corp_init',
                 'ideal_pmnts_sprt_init']

    def __init__(self,
        prcp_corp: List[float],
        prcp_sprt: List[float],
        APR_corp: float,
        APR_sprt: float,
        loan_tnr: float,
        balloon_params: Tuple,
        collection_freq: int,
        annual_cmpnd_prds: int=360,
        prv_pmnts_corp: List[float]=[],
        prv_pmnts_sprt: List[float]=[],
        subsprt_info: Any={},
        APR_pnlt: float=0,
        max_slope: float=np.inf,
        collection_dates: List[dt.datetime] = [],
        sig_figs_2rnd: int = DEFAULT_PRECISION_MONEY,
        tol: float = 10**(-DEFAULT_PRECISION_MONEY-1),
        num_CPUs = 1):
    
        """
        The balloon coupon is at the core of how the credit-line product works. A small minimum is due every period and a
        balloon payment is due at the end representing the lion's share of the principal
        However it is in fact two different coupons stitched together
        (1) an annuity coupon representing all that happens from the start to the penultimate period
        (2) ballon coupon for the final balloon payment

        Parameters (all same as coupon except balloon params)
        ----------
        balloon_params (tuple): Ideally a named tuple triple as follows
                                (1) tenor_annuity (float): the annuity coupon is almost the same as the balloon coupon but with a different tenor
                                                           the tenor is computed to satisfy the restriction in balloon_params (i.e. a certain % of
                                                           principal is due on or after the period with the desired ballon payment)
                                (2) fst_pmnt_pct_annuity (float): typically the first period is of a different length than the rest due to the timing of the
                                                                  disbursal. by multiplying the first period repayment by this coefficient, all payments across
                                                                  all periods should be the same
                                (3) pct_prcp_annuity (float): give a desired payment per month and tenor, what multiplier of the total principal would achieve that
                                This is the output of the static method calc_balloon_coupon_parameters
                                However if it is a tuple such as (value, value_type) the object will invoke calc_balloon_coupon_parameters
                                to compute the proper parameters
        
        Methods
        -------
        update: updates coupon when new repayments occur
        fetch_repayment_amount: given a period or date (if loan was parameterized with repayment dates) gives the amount due or full repayment
        calc_balloon_coupon_parameters: see above
        """

        # basic assertion
        assert len(prv_pmnts_corp)==len(prv_pmnts_sprt), \
                "payments of different length for corpus vs supporters"
        
        # parse balloon_params
        if hasattr(balloon_params,'_fields') and \
           balloon_params._fields==('tenor_annuity', 'pct_prcp_annuity','balloon_params'):
            self.tenor_annuity = balloon_params.tenor_annuity
            self.pct_prcp_annuity = balloon_params.pct_prcp_annuity
            self.fst_pmnt_pct_annuity = balloon_params.fst_pmnt_pct_annuity
        else:
            x,y,z = self.calc_balloon_coupon_parameters(
                            param_value =  balloon_params[0],
                            prcp_corp = prcp_corp,
                            prcp_sprt = prcp_sprt,
                            APR_corp = APR_corp,
                            APR_sprt = APR_sprt,
                            loan_tnr = loan_tnr,
                            collection_freq = collection_freq,
                            annual_cmpnd_prds = annual_cmpnd_prds,
                            subsprt_info = subsprt_info,
                            APR_pnlt = APR_pnlt,
                            sig_figs_2rnd = sig_figs_2rnd,
                            tol = tol,
                            num_CPUs = num_CPUs,
                            param_type = balloon_params[1])
            self.tenor_annuity = x
            self.fst_pmnt_pct_annuity = y
            self.pct_prcp_annuity = z

        # attributes to store
        self.loan_tnr = loan_tnr

        # attributes we only need for initialization and can forget about
        init_attr = {'APR_corp': APR_corp,
                     'APR_sprt': APR_sprt,
                     'APR_pnlt': APR_pnlt,
                     'prcp_corp_init': prcp_corp,
                     'prcp_sprt_init': prcp_sprt,
                     'sig_figs_2rnd' : sig_figs_2rnd,
                     'tol': tol,
                     'max_slope': max_slope*(loan_tnr>1),
                     'num_CPUs': num_CPUs,
                     'annual_cmpnd_prds': annual_cmpnd_prds,
                     'collection_freq': collection_freq,
                     'collection_dates': collection_dates,
                     'loan_tnr': loan_tnr,
                     'subsprt_info': subsprt_info,
                     'prcp_corp_annuity': prcp_corp * self.pct_prcp_annuity,
                     'prcp_sprt_annuity': prcp_sprt * self.pct_prcp_annuity}

        # store collection dates
        if len(collection_dates)==0:
            # otherwise we enumerate dates by the tenor and colleciont freq
            collection_dates = np.arange(loan_tnr % collection_freq,
                                          loan_tnr+1, collection_freq)
            collection_dates = np.pad(collection_dates[collection_dates>0],(1,0))
        
        self.collection_dict = {date:(None,None) for date in collection_dates}
        self.collection_dict[collection_dates[0]] = tuple((0,0))

        # used by creditLine -- container for repayments (same as collection but diff structure)
        self.repayment_dict = defaultdict(tuple)

        # initialize coupons
        self._calc_init_coupons(init_attr)
        
        # update if repayments
        if len(prv_pmnts_corp)>0:
            self.update(prv_pmnts_corp,prv_pmnts_sprt)
    
    def _calc_init_coupons(self,init_attr):
        """
        instantiates the annuity and balloon coupons

        Parameters
        ----------
        init_attr (dict): dict of initial attributes to instantite coupon objects
        """

        def init_coupon_annuity():
            return Coupon(prcp_corp = init_attr['prcp_corp_init']*pct_prcp_annuity,
                         prcp_sprt = init_attr['prcp_sprt_init']*pct_prcp_annuity,
                         APR_corp = init_attr['APR_corp'],
                         APR_sprt = init_attr['APR_sprt'],
                         loan_tnr = self.tenor_annuity,
                         prv_pmnts_corp = [],
                         prv_pmnts_sprt = [],
                         subsprt_info = init_attr['subsprt_info'],
                         APR_pnlt = init_attr['APR_pnlt'],
                         max_slope = init_attr['max_slope'],
                         annual_cmpnd_prds = init_attr['annual_cmpnd_prds'],
                         collection_freq = init_attr['collection_freq'],
                         collection_dates = init_attr['collection_dates'],
                         sig_figs_2rnd = init_attr['sig_figs_2rnd'],
                         tol = init_attr['tol'],
                         num_CPUs = init_attr['num_CPUs'])

        # calc annuity coupon for single disbursal
        if self.tenor_annuity==self.loan_tnr and self.pct_prcp_annuity==0:
            pct_prcp_annuity = 0
        else:
            pct_prcp_annuity = 1

        #init annuity coupon
        self.coupon_annuity = init_coupon_annuity()
        if self.tenor_annuity==self.loan_tnr and self.pct_prcp_annuity==1:
            self.coupon_balloon = self.coupon_annuity
        
        # more complex procedure if ballon_coupon needed
        else: 
            # collections beforehand (multiply by the coef that makes all payments equal)
            indx = np.ceil(self.loan_tnr).astype(int)-1
            pmnt_corp_t0 = self.coupon_annuity.corp_pmnts[0]*self.fst_pmnt_pct_annuity
            pmnt_sprt_t0 = self.coupon_annuity.sprt_pmnts[0]*self.fst_pmnt_pct_annuity            
            # adjust such that min criteria are satisfied
            min_pmnt_corp_t0 = self.coupon_annuity.prcp_corp*self.coupon_annuity.PPR_corp
            min_pmnt_sprt_t0 = self.coupon_annuity.prcp_sprt*self.coupon_annuity.PPR_sprt
            # adjust
            delta_pmnt_sprt = min(0,pmnt_sprt_t0-min_pmnt_sprt_t0)
            pmnt_sprt_t0 = max(pmnt_sprt_t0,min_pmnt_sprt_t0)
            pmnt_corp_t0 = max(pmnt_corp_t0+delta_pmnt_sprt,min_pmnt_corp_t0)


            self.coupon_annuity._update_pmnts_byPrd(pmnts_perPrd_corp=[pmnt_corp_t0],
                                                    pmnts_perPrd_sprt=[pmnt_sprt_t0])
            
            # initialize balloon coupon
            self.coupon_balloon = Coupon(prcp_corp = init_attr['prcp_corp_init'],
                                        prcp_sprt = init_attr['prcp_sprt_init'],
                                        APR_corp = init_attr['APR_corp'],
                                        APR_sprt = init_attr['APR_sprt'],
                                        loan_tnr = self.loan_tnr,
                                        prv_pmnts_corp = self.coupon_annuity.corp_pmnt_perCollect[0:indx].copy(),
                                        prv_pmnts_sprt = self.coupon_annuity.sprt_pmnt_perCollect[0:indx].copy(),
                                        subsprt_info = init_attr['subsprt_info'],
                                        APR_pnlt = 0,
                                        max_slope = 0,
                                        annual_cmpnd_prds = init_attr['annual_cmpnd_prds'],
                                        collection_freq = init_attr['collection_freq'],
                                        collection_dates = init_attr['collection_dates'],
                                        sig_figs_2rnd = init_attr['sig_figs_2rnd'],
                                        tol = init_attr['tol'],
                                        num_CPUs = init_attr['num_CPUs'])

            # update balloon coupon with the correct payments info
            indx = len(self.coupon_balloon.prv_pmnts_corp)
            self.coupon_balloon._update_pmnts_byPrd(self.coupon_annuity.corp_pmnts[0:indx], 
                                                    self.coupon_annuity.sprt_pmnts[0:indx],
                                                    set_ideal = True)
            
            # reinitiate annuity coupon without the previous payment
            self.coupon_annuity = init_coupon_annuity()

        # store ideal payments
        self.ideal_pmnts_corp_init = self.coupon_balloon.corp_pmnt_perCollect
        self.ideal_pmnts_sprt_init = self.coupon_balloon.sprt_pmnt_perCollect
            
    def update(self,
        collections_corp: List=[],
        collections_sprt: List=[]):
        """
        updates coupon with new repayments

        Parameters
        ----------
        collections_corp (List[Repayment]): all previous collections into the corpus tranche
        collections_sprt (List[Repayment]): all previous collections into the supporter tranche

        this also works just being called with List[float] instead of repayment class
        """

        # combine collections with previous collections
        combined_dict = LoanMath.convert_regular_payments_2_combined_dict(
                            list(collections_corp),list(collections_sprt),list(self.collection_dict.keys())[0],
                            keep_dates=True,prv_repayments_dict=self.collection_dict,
                            collection_dates=list(self.collection_dict.keys())[1:])
        
        # check coalesced dict against the original in memory
        combined = set(combined_dict.items())
        diff_items = combined.difference(set(self.collection_dict.items()))

        if bool(diff_items):
            #  update collections dict
            self.collection_dict = dict(sorted(combined,key=lambda x: x[0]))

            # update annuity coupon
            self.coupon_annuity.update(collections_corp = list(collections_corp),
                                       collections_sprt = list(collections_sprt))
            
            if self.tenor_annuity==self.loan_tnr:
                self.coupon_balloon = self.coupon_annuity
            else:
                # indx of previous payments (always 1-ballon_payment unless at last period)
                indx = max(len(self.coupon_balloon.prv_pmnts_corp),len(collections_corp))
                # collections beforehand (remove penalties)
                payments_corp_adj = self.coupon_annuity.corp_pmnts[0:indx]\
                                     - np.where(self.coupon_annuity.corp_pnlt_perPrd[0:indx]<0,0,
                                                self.coupon_annuity.corp_pnlt_perPrd[0:indx])
                payments_sprt_adj = self.coupon_annuity.sprt_pmnts[0:indx]\
                                     - np.where(self.coupon_annuity.sprt_pnlt_perPrd[0:indx]<0,0,
                                                self.coupon_annuity.sprt_pnlt_perPrd[0:indx])
                
                # update balloon coupon
                self.coupon_balloon._update_pmnts_byPrd(pmnts_perPrd_corp = payments_corp_adj,
                                                        pmnts_perPrd_sprt = payments_sprt_adj,
                                                        indx_prd_2_collect = self.coupon_annuity.indx_prd_2_collect[
                                                            self.coupon_annuity.indx_prd_2_collect<=max(self.coupon_balloon.indx_prd_2_collect)],
                                                        set_ideal = False)
            
            # update repayment_dict
            # for date,item in diff_items:
            #    self._update_repayment_dict(date,overwrite=True)
    
    def _update_repayment_dict(self,repayment_date,repay_amt_corp = None,repay_amt_sprt = None, overwrite=False):

        # named tuples to fill dict
        Repay = namedtuple('Repay',['owed','paid','prcp_outstand'])
        repay = namedtuple('repay',['corp', 'sprt'])

        # get values from collections_dict
        if repay_amt_corp is None and repay_amt_sprt is None:
            repay_amt_corp, repay_amt_sprt = self.collection_dict[repayment_date]

        if repayment_date not in self.repayment_dict.keys() or overwrite:
            corp_owed, sprt_owed = self.fetch_repayment_amount(repayment_date)
            corp_full_repay, sprt_full_repay = self.fetch_repayment_amount(repayment_date,True)
            self.repayment_dict[repayment_date] = repay(Repay(corp_owed,None,corp_full_repay-corp_owed),
                                                        Repay(sprt_owed,None,sprt_full_repay-sprt_owed))
        
        if repay_amt_corp is not None and repay_amt_sprt is not None:
            corp_owed = self.repayment_dict[repayment_date].corp.owed
            sprt_owed = self.repayment_dict[repayment_date].sprt.owed
            corp_prcp_outstand = self.repayment_dict[repayment_date].corp.prcp_outstand
            sprt_prcp_outstand = self.repayment_dict[repayment_date].sprt.prcp_outstand

            self.repayment_dict[repayment_date] = repay(Repay(corp_owed,repay_amt_corp,corp_prcp_outstand),
                                                        Repay(sprt_owed,repay_amt_sprt,sprt_prcp_outstand))
            
    @staticmethod
    def calc_balloon_coupon_parameters(
            param_value: float,
            prcp_corp: float,
            prcp_sprt: float,
            APR_corp: float,
            APR_sprt: float,
            loan_tnr: float,
            collection_freq: int,
            annual_cmpnd_prds: int,
            subsprt_info: Any={},
            APR_pnlt: float=0,
            sig_figs_2rnd: int = DEFAULT_PRECISION_MONEY,
            tol: float = 10**(-DEFAULT_PRECISION_MONEY-1),
            num_CPUs = 1,
            param_type = 'pct_balloon'):
        """
        Computes the three desired parameters for the ballon couupon

        Parameters
        ----------
        see coupon.py for documentation
        param_value: first value of balloon_params
        param_type: second value of ballon_params indicating what the first param means

        Returns
        -------
        (1) tenor_annuity (float)
        (2) fst_pmnt_pct_annuity (float<1)
        (3) pctp_prcp_annuity (float<1)
        see above for definitions
        """

        # function to invoke coupon
        def gen_coupon(tenor_annuity,pct_prcp_annuity=1):
            return Coupon(prcp_corp = prcp_corp*pct_prcp_annuity,
                        prcp_sprt = prcp_sprt*pct_prcp_annuity,
                        APR_corp = APR_corp,
                        APR_sprt = APR_sprt,
                        loan_tnr = tenor_annuity,
                        prv_pmnts_corp = [],
                        prv_pmnts_sprt = [],
                        subsprt_info = subsprt_info,
                        APR_pnlt = APR_pnlt,
                        max_slope = 0, #init_attr['max_slope'],
                        annual_cmpnd_prds = annual_cmpnd_prds,
                        collection_freq = collection_freq,
                        sig_figs_2rnd = sig_figs_2rnd,
                        tol = tol,
                        num_CPUs = num_CPUs)
        
        # named tuple for output
        balloon_params = namedtuple('balloon_params',['tenor_annuity','fst_pmnt_pct_annuity','pct_prcp_annuity'])

        # pct of principal to be covered by first loan_tnr-1 periods
        prcp_covered_annuity = (1-param_value)*(prcp_corp+prcp_sprt)
        # collections beforehand
        indx = np.ceil(loan_tnr).astype(int)-1
        # being lazy and brute-force solving it
        def function_2_solve_pct_ballon(tenor_annuity):
            coupon = gen_coupon(tenor_annuity[0])
            prcp_covered_hat = coupon.corp_prcp_perCollect[0:indx].sum() \
                                + coupon.sprt_prcp_perCollect[0:indx].sum()
            return (prcp_covered_hat - prcp_covered_annuity)**2
            
        # convert pct_min_pmnt to actual amount paid
        min_pmnt = param_value*(prcp_corp+prcp_sprt)
        # being lazy and brute-force solving it
        def function_2_solve_pct_min_pmnt(tenor_annuity):
            coupon = gen_coupon(tenor_annuity[0])
            pmnt_hat = coupon.corp_prcp_perCollect[1]\
                        + coupon.sprt_prcp_perCollect[1]
            return (pmnt_hat - min_pmnt)**2

        # Find Roots
        if param_type=='pct_balloon':
            if param_value==0:
                return  balloon_params(loan_tnr,1)
            elif param_value==1:
                return balloon_params(loan_tnr,0)
            else:
                tenor_annuity = optimize.differential_evolution(
                                    function_2_solve_pct_ballon,
                                    bounds = [(np.ceil(loan_tnr).astype(int),
                                                np.ceil(loan_tnr/(1-param_value)*2).astype(int))],
                                    workers = num_CPUs)
        elif param_type=='pct_min_pmnt':
            if param_value==0:
                return balloon_params(loan_tnr,0)
            else:
                tenor_annuity = optimize.differential_evolution(
                                    function_2_solve_pct_min_pmnt,
                                    bounds = [(np.ceil(loan_tnr).astype(int),
                                                np.ceil((prcp_corp+prcp_sprt)/min_pmnt*2).astype(int))],
                                    workers = num_CPUs)
        # get tenor                        
        tenor_annuity = tenor_annuity.x[0]

        # adjust principal so tenor is integer
        coupon = gen_coupon(tenor_annuity)
        tenor_annuity_ceil = np.ceil(tenor_annuity)
        min_pmnt = coupon.corp_prcp_perCollect[1]+ coupon.sprt_prcp_perCollect[1]
        # being lazy and brute-force solving it
        def function_2_solve_pct_prcp(pct_prcp_annuity):
            coupon = gen_coupon(tenor_annuity_ceil,pct_prcp_annuity[0])
            pmnt_hat = coupon.corp_prcp_perCollect[1]\
                        + coupon.sprt_prcp_perCollect[1]
            return pmnt_hat - min_pmnt
        pct_prcp_annuity = optimize.fsolve(function_2_solve_pct_prcp, (prcp_corp+prcp_sprt)/min_pmnt)

        # adjust first period payment so all payments are same
        def function_2_solve_pmnt_same(fst_pmnt_pct):
            coupon = gen_coupon(tenor_annuity)
            pmnt_corp_t0 = coupon.corp_pmnts[0]*fst_pmnt_pct[0]
            pmnt_sprt_t0 = coupon.sprt_pmnts[0]*fst_pmnt_pct[0]
            coupon._update_pmnts_byPrd(pmnts_perPrd_corp=[pmnt_corp_t0],
                                       pmnts_perPrd_sprt=[pmnt_sprt_t0])
            pmnt_corp_t1 = coupon.corp_pmnts[1]
            pmnt_sprt_t1 = coupon.sprt_pmnts[1]

            return ((pmnt_sprt_t1+pmnt_corp_t1)-(pmnt_corp_t0+pmnt_sprt_t0))**2
        fst_pmnt_pct = optimize.differential_evolution(
                                    function_2_solve_pmnt_same,
                                    bounds = [(1,1/coupon.fst_prd_len)],
                                    workers = num_CPUs)
        
        #return
        return  balloon_params(tenor_annuity,fst_pmnt_pct.x[0],pct_prcp_annuity[0])
    
    def fetch_repayment_amount(self,repayment_date,full_repay=False):
        """
        returns the repayment amount for a period and total amount to repay to settle loan
        in this case the ballon_coupon is the reference base

        Parameters
        ----------
        repayment_date (dt.datetime or int): can be either an integer for the period or the date if loan parameterized with repayment dates
        full_repay (bool): return full_repayment amount or solely amount due this period

        Returns
        -------
        tuple by corpus, supporter 
        """
        
        return self.coupon_balloon.fetch_repayment_amount(repayment_date,full_repay)

    @property
    def num_prv_collect(self):
        return len([val for val in list(self.collection_dict.values())[1:] if val[0] is not None])
    
    @property
    def num_prv_pmnts(self):
        return self.num_prv_collect
    
    @property
    def corp_pmnt_perCollect(self):
        return self.coupon_balloon.corp_pmnt_perCollect
    
    @property
    def corp_prcp_perCollect(self):
        return self.coupon_balloon.corp_prcp_perCollect
    
    @property
    def corp_intr_perCollect(self):
        return self.coupon_balloon.corp_intr_perCollect

    @property
    def sprt_pmnt_perCollect(self):
        return self.coupon_balloon.sprt_pmnt_perCollect
    
    @property
    def sprt_prcp_perCollect(self):
        return self.coupon_balloon.sprt_prcp_perCollect
    
    @property
    def sprt_intr_perCollect(self):
        return self.coupon_balloon.sprt_intr_perCollect
    
    @property
    def corp_pnlt_perCollect(self):
        return np.append(self.coupon_annuity.corp_pnlt_perCollect[0:-1],
                         self.coupon_balloon.corp_pnlt_perCollect[-1])

    @property
    def sprt_pnlt_perCollect(self):
        return np.append(self.coupon_annuity.sprt_pnlt_perCollect[0:-1],
                         self.coupon_balloon.sprt_pnlt_perCollect[-1])
    
    @property
    def collection_dates(self):
        return self.collection_dict.keys()
    
    @property
    def start_date(self):
        return self.collection_dict.keys()[0]
    
    @property
    def days_per_period(self):
        return self.coupon_balloon.days_per_period
    
    @property
    def prcp_corp(self):
        return self.coupon_balloon.prcp_corp
    
    @property
    def prcp_sprt(self):
        return self.coupon_balloon.prcp_sprt

    @property
    def prcp_corp_annuity(self):
        return self.coupon_annuity.prcp_corp
    
    @property
    def sprt_sprt_annuity(self):
        return self.coupon_annuity.prcp_sprt

    @property
    def corp_collect_current(self):
        return self.corp_pmnt_perCollect[self.num_prv_collect]
    
    @property
    def sprt_collect_current(self):
        return self.sprt_pmnt_perCollect[self.num_prv_collect]

    @property
    def corp_collect_full_repay(self):
        corp, sprt = self.fetch_repayment_amount(self.num_prv_collect+1,True)
        return corp

    @property
    def sprt_collect_full_repay(self):
        corp, sprt = self.fetch_repayment_amount(self.num_prv_collect+1,True)
        return sprt

    # below properties are wrong
    @property
    def corp_intr_owed(self):
        return self.corp_intr_perCollect[self.num_prv_collect:].sum()

    @property
    def corp_intr_paid(self):
        return self.corp_intr_perCollect[0:self.num_prv_collect].sum()
    
    @property
    def corp_prcp_owed(self):
        return self.corp_prcp_perCollect[self.num_prv_collect:].sum()

    @property
    def corp_prcp_paid(self):
        return self.corp_prcp_perCollect[0:self.num_prv_collect].sum()

    @property
    def sprt_intr_owed(self):
        return self.sprt_intr_perCollect[self.num_prv_collect:].sum()

    @property
    def sprt_intr_paid(self):
        return self.sprt_intr_perCollect[0:self.num_prv_collect].sum()
    
    @property
    def sprt_prcp_owed(self):
        return self.sprt_prcp_perCollect[self.num_prv_collect:].sum()

    @property
    def sprt_prcp_paid(self):
        return self.sprt_prcp_perCollect[0:self.num_prv_collect].sum()
    
    def to_dict(self):
        return {
        'corp_collections': self.corp_pmnt_perCollect,
        'corp_collect_full_repay': self.corp_collect_full_repay,
        'corp_collect_current': self.corp_collect_current,
        'corp_prcp_perCollect': self.corp_prcp_perCollect,
        'corp_intr_perCollect': self.corp_intr_perCollect,
        'corp_pnlt_perCollect': self.corp_pnlt_perCollect,
        'sprt_collections': self.sprt_pmnt_perCollect,
        'sprt_collect_full_repay': self.sprt_collect_full_repay,
        'sprt_collect_current': self.sprt_collect_current,
        'sprt_prcp_perCollect': self.sprt_prcp_perCollect,
        'sprt_intr_perCollect': self.sprt_intr_perCollect,
        'sprt_pnlt_perCollect': self.sprt_pnlt_perCollect,
        'corp_intr_owed': self.corp_intr_owed,
        'corp_intr_paid': self.corp_intr_paid,
        'corp_prcp_owed': self.corp_prcp_owed,
        'corp_prcp_paid': self.corp_prcp_paid,
        'sprt_intr_owed': self.sprt_intr_owed,
        'sprt_intr_paid': self.sprt_intr_paid,
        'sprt_prcp_owed': self.sprt_prcp_owed,
        'sprt_prcp_paid': self.sprt_prcp_paid,
        'collections_by_prd': self.collection_dict
        }

# payments_corp = self.coupon_annuity.corp_pmnts.copy()
# payments_corp[0] = payments_corp[0]/self.coupon_annuity.fst_prd_len
# payments_sprt = self.coupon_annuity.sprt_pmnts.copy()
# payments_sprt[0] = payments_sprt[0]/self.coupon_annuity.fst_prd_len
# collections_corp = splitsum(payments_corp,
#                             self.coupon_annuity.collection_freq,
#                             self.coupon_annuity.indx_prd_2_collect)
# collections_sprt = splitsum(payments_sprt,
#                             self.coupon_annuity.collection_freq,
#                             self.coupon_annuity.indx_prd_2_collect)

# # modify collections to deal with different fst_prd_len
# indx = self.coupon_annuity.indx_prd_2_collect[len(collections_corp)]
# payments_corp = calc_pmnts_per_collect(list(collections_corp)[-1],self.coupon_annuity.ideal_pmnts_corp[0:indx].tolist())
# payments_corp[0] = payments_corp[0]*self.coupon_annuity.fst_prd_len
# payments_sprt = calc_pmnts_per_collect(list(collections_sprt)[-1],self.coupon_annuity.ideal_pmnts_sprt[0:indx].tolist())
# payments_sprt[0] = payments_sprt[0]*self.coupon_annuity.fst_prd_len
# collections_corp_adj = splitsum(payments_corp,
#                                 self.coupon_annuity.collection_freq,
#                                 self.coupon_annuity.indx_prd_2_collect)
# collections_sprt_adj = splitsum(payments_sprt,
#                                 self.coupon_annuity.collection_freq,
#                                 self.coupon_annuity.indx_prd_2_collect)
# # extract payments - penalties
# payments_corp = self.coupon_annuity.corp_pmnts.copy()
# payments_corp[0] = payments_corp[0]/self.coupon_annuity.fst_prd_len
# payments_sprt = self.coupon_annuity.sprt_pmnts.copy()
# payments_sprt[0] = payments_sprt[0]/self.coupon_annuity.fst_prd_len
#  # helper functions
#  def calc_pmnts_per_collect(collect_amt,ideal_pmnts):
#      num_pmnts = len(ideal_pmnts)
#      indx = min(np.searchsorted(np.cumsum(ideal_pmnts),collect_amt),num_pmnts-1)
#      #ideal_pmnts = [ideal_pmnts[i] for i in range(0,(indx+1))]
#      pmnt_vec = np.pad(ideal_pmnts[0:(indx+1)],(0,(num_pmnts-(indx+1))))
#      pmnt_vec[indx] = collect_amt-np.sum(ideal_pmnts[0:indx])
#      return pmnt_vec

# def splitsum(vec,collection_freq,indx_prd_2_collect):
#     if collection_freq==1:
#         return vec
#     else:
#         return np.fromiter(map(np.sum,
#                                 np.split(vec,indx_prd_2_collect[1:-1])),
#                             dtype=np.float)