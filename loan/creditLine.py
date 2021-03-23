from operator import truediv
from typing import Any, List, Tuple, Dict
import numpy as np
from numpy.lib.polynomial import _raise_power
import pandas as pd
import datetime as dt

from iteround import saferound
from collections import defaultdict, namedtuple, Counter, OrderedDict
from scipy import optimize, special

from loan.LoanMath import LoanMath
from loan.loan import Loan
from loan.couponTypes import BalloonCoupon
from common.loan import Repayment
from common.constant import (DEFAULT_DISCOUNT_APR,
                                     DEFAULT_PRECISION_MATH_OPERATIONS,
                                     DEFAULT_PRECISION_MONEY,
                                     DEFAULT_SUPPORTER_LAG)

class CreditLine:
    __slots__ = ['APR_corp',
                 'APR_sprt',
                 'APR_pnlt',
                 'loan_tnr',
                 'pct_prcp_annuity'
                 'subsprt_info',
                 'max_slope',
                 'sig_figs_2rnd',
                 'tol',
                 'num_CPUs',
                 'collection_freq',
                 'annual_cmpnd_prds',
                 'days_per_period',
                 'days_per_collection',
                 'max_credit_line',
                 'start_date',
                 'disbursals',
                 'disbursals_dict',
                 'collections_dict',
                 'disbursal_repayments',
                 'new_disbursals',
                 'disbursals_last_repaid',
                 'next_collection_date',
                 'corp_pmnt_perCollect',
                 'corp_prcp_perCollect',
                 'corp_intr_perCollect',
                 'corp_pnlt_perCollect',
                 'sprt_pmnt_perCollect',
                 'sprt_prcp_perCollect',
                 'sprt_intr_perCollect',
                 'sprt_pnlt_perCollect']

    def __init__(self,
        APR_corp: float,
        APR_sprt: float,
        loan_tnr: float,
        max_credit_line: float,
        start_date: dt.datetime,
        sprt_shr: float,
        sprt_cash_encumbr: float,
        sprt_ptfl_encumbr: float,
        brw_collateral: float,
        collection_freq: int=15,
        annual_cmpnd_prds: int=360,
        sprt_lag: int = DEFAULT_SUPPORTER_LAG,
        disbursals: List[Repayment]=[],
        repayments: List[Repayment]=[],
        subsprt_info: Any={},
        balloon_params: Any = (0.5,'pct_balloon'), 
        APR_disc: float = DEFAULT_DISCOUNT_APR,
        APR_pnlt: float = 0,
        max_slope: float=np.inf,
        sig_figs_2rnd: int = DEFAULT_PRECISION_MONEY,
        tol: float = 10**(-DEFAULT_PRECISION_MONEY-1),
        num_CPUs = 1):
        """
        a credit line consists of multiple loans
        """

        # save attributes needed to instantiate a disbursal
        self.APR_corp = APR_corp
        self.APR_sprt = APR_sprt
        self.APR_pnlt = APR_pnlt
        self.APR_disc = APR_disc
        self.loan_tnr = loan_tnr
        self.sprt_lag = sprt_lag
        self.sprt_shr = sprt_shr
        self.subsprt_info = subsprt_info
        self.max_slope = max_slope
        self.sig_figs_2rnd = sig_figs_2rnd
        self.tol = tol
        self.num_CPUs = num_CPUs

        # collaterals and encumbrances
        self.sprt_cash_encumbr_init = sprt_cash_encumbr
        self.sprt_ptfl_encumbr_init = sprt_ptfl_encumbr
        self.brw_collateral_init = brw_collateral
        self.sprt_cash_encumbr = sprt_cash_encumbr
        self.sprt_ptfl_encumbr = sprt_ptfl_encumbr
        self.brw_collateral = brw_collateral

        # save temporal attributes
        self.collection_freq = collection_freq
        self.annual_cmpnd_prds = annual_cmpnd_prds
        self.days_per_period = np.round(360/annual_cmpnd_prds)
        self.days_per_collection = collection_freq*self.days_per_period

        # specific to this object
        self.max_credit_line = max_credit_line
        self.start_date = start_date

        # initalize dicts that form core logic
        self.disbursals = {}
        self.disbursals_dict = {}
        self.collections_dict = {}
        self.disbursal_repayments = defaultdict(List)

        # IDs of newly updated
        self.new_disbursals = []
        self.disbursals_last_repaid = []

        # Parse ballon parameters
        if hasattr(balloon_params,'_fields') and \
           balloon_params._fields==('tenor_annuity', 'pct_prcp_annuity','balloon_params'):
            self.balloon_params = balloon_params
        else:
            self.balloon_params = BalloonCoupon.calc_balloon_coupon_parameters(
                                        param_value =  balloon_params[0],
                                        prcp_corp = self.max_credit_line*(1-sprt_shr),
                                        prcp_sprt = self.max_credit_line*sprt_shr,
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

        # update
        if bool(disbursals):
            self.update(disbursals,repayments)
    
    def _calc_collections_dates(self,disbursal_date):
        # next collection date proceeding disbursal date
        fst_collection_date = LoanMath.calc_collection_dates(self.start_date,
                                                             disbursal_date,
                                                             self.days_per_collection,
                                                             shift=True)[-1]
        # collections starting from that point
        dates = LoanMath.calc_collection_dates(fst_collection_date,
                                               fst_collection_date,
                                               self.days_per_collection,
                                               self.loan_tnr)
        # tenor is different for the disbursal as a result
        disbursal_tnr = (dates[-1]-disbursal_date).days/self.days_per_collection

        return dates, disbursal_tnr

    def _create_disbursal(self,disbursal_date,principal):

        #convert disbursal date to normal date
        # disbursal_date = self.start_date+dt.timedelta(days=disbursal_period*self.days_per_period)
        # calc collection dates    
        collect_dates, disbursal_tnr = self._calc_collections_dates(self,disbursal_date)
        # append start date
        collect_dates = [disbursal_date]+collect_dates
        # produce object 
        disbursal = Loan(corp_APR = self.APR_corp,
                         sprt_APR = self.APR_sprt,
                         loan_amt = principal,
                         loan_tnr = disbursal_tnr,
                         sprt_shr = self.sprt_shr,
                         sprt_cash_encumbr = self.sprt_cash_encumbr*principal/self.max_credit_line,
                         sprt_ptfl_encumbr = self.sprt_ptfl_encumbr*principal/self.max_credit_line,
                         brw_collateral = self.brw_collateral*principal/self.max_credit_line,
                         repayments = [],
                         penalty_APR = self.APR_pnlt,
                         sprt_lag = self.sprt_lag,
                         discount_APR = self.APR_disc,
                         subsprt_info = self.subsprt_info,
                         balloon_params = self.balloon_params,
                         max_slope = self.max_slope,
                         annual_cmpnd_prds = self.annual_cmpnd_prds,
                         collection_dates = collect_dates,
                         collection_freq = self.collection_freq,
                         id = "" )
        
        # add to disbursals_dict
        self.disbursals_dict[disbursal_date] = principal
        # update disbursal_repayments
        for date in collect_dates:
            self.disbursal_repayments[date].extend(disbursal_date)

        return disbursal
    
    def _fetch_active_disbursal_IDs(self,repayment_date):
        
        # get disbursals
        if repayment_date in self.disbursal_repayments.keys():
            disbursal_IDs = self.disbursal_repayments[repayment_date]
        else: # choose the closest proceeding collection date
            nxt_collect_indx = np.where(self.disbursal_repayments.keys()>repayment_date)[0][0]
            nxt_collect_date = self.disbursal_repayments.keys()[nxt_collect_indx]
            disbursal_IDs = self.disbursal_repayments[nxt_collect_date]
        
        # filter disbursals that didnt start on that date (IDs are dates)
        disbursal_IDs = sorted([ID for ID in disbursal_IDs if repayment_date>ID])

        return disbursal_IDs
    
    def _fetch_repayments_by_disbursal(self,repayment_date):
        
        disbursal_IDs = self._fetch_active_disbursal_IDs(repayment_date)

        # fetch desired repayments
        for ID in disbursal_IDs:
            self.disbursals[ID]._update_repayment_dict(repayment_date)

        corp_owed = [self.disbursals[ID].repayment_dict[repayment_date].corp.owed for ID in disbursal_IDs]
        sprt_owed = [self.disbursals[ID].repayment_dict[repayment_date].sprt.owed for ID in disbursal_IDs]
        corp_prcp_outstand = [self.disbursals[ID].repayment_dict[repayment_date].corp.prcp_outstand  for ID in disbursal_IDs]
        sprt_prcp_outstand  = [self.disbursals[ID].repayment_dict[repayment_date].sprt.prcp_outstand  for ID in disbursal_IDs]

        return disbursal_IDs, corp_owed, sprt_owed, corp_prcp_outstand, sprt_prcp_outstand

    def _allocate_repayment_to_disbursals(self,repayment_date,corp_repay_amt,sprt_repay_amt):

        # helper function that defines amount filled and amount remaining
        def fill_helper(amt_2_fill, amt_on_hand):
            amt_filled = min(amt_2_fill, amt_on_hand)
            new_amt_on_hand = amt_on_hand - amt_filled
            return amt_filled, new_amt_on_hand

        def fill_allocator(pmnt_amt,owed_amt_vec):
            if isinstance(owed_amt_vec,dict):
                owed_amt_vec = [owed_amt_vec[key] for key in sorted(owed_amt_vec.keys())]
            allocation_vec = np.zeros(len(owed_amt_vec))
            for i in range(0,len(owed_amt_vec)):
                allocation_vec[i], pmnt_amt = fill_helper(owed_amt_vec[i], pmnt_amt)
            return allocation_vec, pmnt_amt

        # fetch amounts owed
        disbursal_IDs, corp_owed, sprt_owed, corp_prcp_outstand, sprt_prcp_outstand = \
            self._fetch_repayments_by_disbursal(repayment_date)

        # calc allocations
        corp_owed_allocate, corp_repay_remain = fill_allocator(corp_repay_amt,corp_owed)
        corp_prcp_outstand_allocate, corp_repay_remain = fill_allocator(corp_repay_remain,corp_prcp_outstand)
        sprt_owed_allocate, sprt_repay_remain = fill_allocator(sprt_repay_amt,sprt_owed)
        sprt_prcp_outstand_allocate, sprt_repay_remain = fill_allocator(sprt_repay_remain,sprt_prcp_outstand)

        # combine
        corp_allocate = corp_owed_allocate+corp_prcp_outstand_allocate
        sprt_allocate = sprt_owed_allocate+sprt_prcp_outstand_allocate

        return disbursal_IDs, corp_allocate, sprt_allocate
    
    def _repay_once(self,repayment_date,corp_repay_amt,sprt_repay_amt):

        # retrieve allocations
        disbursal_IDs, corp_allocate, sprt_allocate = \
            self._allocate_repayment_to_disbursals(repayment_date,corp_repay_amt,sprt_repay_amt)

        # update disbursal objects
        for i in range(0,len(disbursal_IDs)):
            ID = disbursal_IDs[i]
            self.disbursals[ID].update(collections_corp=[tuple(repayment_date,corp_allocate[i])],
                                       collections_sprt=[tuple(repayment_date,sprt_allocate[i])])
        
        # update collections dict
        self.collections_dict[repayment_date] = tuple(corp_repay_amt,sprt_repay_amt)

        return disbursal_IDs
    
    def update(self,
        collections_corp: list=[],
        collections_sprt: list=[],
        disbursals_corp : list=[],
        disbursals_sprt : list=[]):

        # remove disbursals that have been finalized
        for ID in self.disbursals_last_repaid:
            if self.disbursals[ID].corp_prcp_owed==0 and self.disbursals[ID].sprt_prcp_owed==0:
                self.disbursals.pop(ID,None)

        # retrieve new collections
        if bool(collections_corp) and bool(collections_sprt):
            collect_combined = LoanMath.convert_regular_payments_2_combined_dict(
                                    collections_corp,collections_sprt,self.start_date,
                                    keep_dates=True,prv_repayments_dict=self.collections_dict)
            
            # check coalesced dict against the original in memory
            new_collections = dict(set(collect_combined.items()).difference(set(self.collections_dict.items())))
            new_collect_dates = new_collections.keys()
            self.disbursals_last_repaid = []
        else:
            new_collect_dates = []
        
        # retrieve new disbursals
        if bool(disbursals_corp) and bool(disbursals_sprt):
            disburse_combined = LoanMath.convert_regular_payments_2_combined_dict(
                                    disbursals_corp,disbursals_sprt,self.start_date,
                                    keep_dates=True,prv_repayments_dict=self.disbursals_dict)
            
            # check coalesced dict against the original in memory
            new_disbursals = dict(set(disburse_combined.items()).difference(set(self.disbursals_dict.items())))
            new_disburse_dates =  new_disbursals.keys()
            self.new_disbursals = []
        else:
            new_disburse_dates = []

        # execute in order
        for date in np.unique(new_collect_dates+new_disburse_dates):
            if date in new_disburse_dates:
                if new_disbursals[date][0]>0 or new_disbursals[date][1]>0:
                    if np.sum(new_disbursals[date]) > self.max_amount_borrowable:
                        raise ValueError("new disbursals cannot exceed credit line")
                    self.disbursals[date] = self._create_disbursal(date,
                                                                   new_disbursals[date][0],
                                                                   new_disbursals[date][1])
                    self.new_disbursals.extend(date)
            if date in new_collect_dates:
                if new_collections[date][0]>0 or new_collections[date][1]>0:
                    updated_IDs = self._repay_once(date,
                                                   new_collections[date][0],
                                                   new_collections[date][1])
                    self.disbursals_last_repaid.extend(updated_IDs)
        
        # set next collection date
        future_collect_dates = self.disbursal_repayments.keys()[self.disbursal_repayments.keys()>max(self.collections_dict.keys())]
        self.next_collection_date = min(future_collect_dates)

        # update attributes
        self.corp_pmnt_perCollect = self._sum_over_disbursals(self.disbursals.keys(),'corp_pmnt_perCollect')
        self.corp_prcp_perCollect = self._sum_over_disbursals(self.disbursals.keys(),'corp_prcp_perCollect')
        self.corp_intr_perCollect = self._sum_over_disbursals(self.disbursals.keys(),'corp_intr_perCollect')
        self.corp_pnlt_perCollect = self._sum_over_disbursals(self.disbursals.keys(),'corp_pnlt_perCollect')
        self.sprt_pmnt_perCollect = self._sum_over_disbursals(self.disbursals.keys(),'sprt_pmnt_perCollect')
        self.sprt_prcp_perCollect = self._sum_over_disbursals(self.disbursals.keys(),'sprt_prcp_perCollect')
        self.sprt_intr_perCollect = self._sum_over_disbursals(self.disbursals.keys(),'sprt_intr_perCollect')
        self.sprt_pnlt_perCollect = self._sum_over_disbursals(self.disbursals.keys(),'sprt_pnlt_perCollect')
                    
    def fetch_repayment_amount(self,repayment_date,full_repay=False):

        _, corp_owed, sprt_owed, corp_prcp_outstand, sprt_prcp_outstand = \
            self._fetch_repayments_by_disbursal(repayment_date)
        
        corp_owed = np.sum(corp_owed)
        sprt_owed = np.sum(sprt_owed)

        if full_repay:
            corp_owed += np.sum(corp_prcp_outstand)
            sprt_owed += np.sum(sprt_prcp_outstand)
        
        return corp_owed, sprt_owed

    def _sum_over_disbursals(self,disbursal_IDs,attribute):
        
        def attr_as_dict_from_disbursal(ID):
            dates = self.disbursals[ID].collection_dates[1:]
            vec = getattr(self.disubrsals[ID],attribute)
            if hasattr(vec, "__len__"):
                return Counter(dict(zip(dates,vec)))
            else:
                return vec
        
        combined = attr_as_dict_from_disbursal(disbursal_IDs[0])
        for ID in disbursal_IDs[1:]:
            combined = combined + attr_as_dict_from_disbursal(ID)
        
        if hasattr(combined, "__len__"):
            return OrderedDict(sorted(combined.items()))
        else:
            return combined
    
    @property
    def max_amount_borrowable(self):
        return self.max_credit_line - self.corp_prcp_owed - self.sprt_prcp_owed

    @property
    def num_prv_collect(self):
        return len(self.collections_dict)
    
    @property
    def collection_dates(self):
        return self.disbursal_repayments.keys()

    @property
    def corp_collect_current(self): 
        return self._sum_over_disbursals(self.disbursal_repayments[self.next_collection_date],
                                         'corp_collect_current')

    @property
    def corp_intr_owed(self):
        return self._sum_over_disbursals(self.disbursals.keys(),'corp_intr_owed')

    @property
    def corp_intr_paid(self):
        return self._sum_over_disbursals(self.disbursals.keys(),'corp_intr_paid')
    
    @property
    def corp_prcp_owed(self):
        return self._sum_over_disbursals(self.disbursals.keys(),'corp_prcp_owed')

    @property
    def corp_prcp_paid(self):
        return self._sum_over_disbursals(self.disbursals.keys(),'corp_prcp_paid')
    
    @property
    def corp_collect_full_repay(self):
        return self._sum_over_disbursals(self.disbursals.keys(),'corp_collect_full_repay')

    @property
    def sprt_collect_current(self):
        return self._sum_over_disbursals(self.disbursal_repayments[self.next_collection_date],
                                         'sprt_collect_current')

    @property
    def sprt_intr_owed(self):
        return self._sum_over_disbursals(self.disbursals.keys(),'sprt_intr_owed')

    @property
    def sprt_intr_paid(self):
        return self._sum_over_disbursals(self.disbursals.keys(),'sprt_intr_paid')
    
    @property
    def sprt_prcp_owed(self):
        return self._sum_over_disbursals(self.disbursals.keys(),'sprt_prcp_owed')

    @property
    def sprt_prcp_paid(self):
        return self._sum_over_disbursals(self.disbursals.keys(),'sprt_prcp_paid')
    
    @property
    def sprt_collect_full_repay(self):
        return self._sum_over_disbursals(self.disbursals.keys(),'sprt_collect_full_repay')
    
    @property
    def prcp_corp(self):
        return self._sum_over_disbursals(self.disbursals.keys(),'prcp_corp')
    
    @property
    def sprt_corp(self):
        return self._sum_over_disbursals(self.disbursals.keys(),'sprt_corp')

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
