
from typing import Any, List, Tuple, Dict

import copy
import numpy as np
import datetime as dt
from scipy import optimize
from iteround import saferound
from itertools import groupby

# from swarmai.loan.LoanMath import LoanMath
from common.constant import (DEFAULT_DISCOUNT_APR,
                                     DEFAULT_PRECISION_MATH_OPERATIONS,
                                     DEFAULT_PRECISION_MONEY)

class Coupon:
    __slots__ = ['prcp_corp', 
                'prcp_sprt', 
                'max_slope', 
                'sig_figs_2rnd', 
                'tol', 
                'num_CPUs', 
                'APR_corp', 
                'APR_sprt', 
                'APR_pnlt', 
                'PPR_corp', 
                'PPR_sprt', 
                'PPR_pnlt', 
                'prv_collect_sprt', 
                'prv_collect_corp', 
                'num_prv_collect', 
                'num_tot_collect', 
                'days_per_period', 
                'loan_tnr', 
                'loan_tnr_orig', 
                'fst_prd_len', 
                'annual_cmpnd_prds', 
                'collection_freq', 
                'indx_prd_2_collect', 
                'num_prv_pmnts', 
                'collection_dict', 
                'prv_pmnts_sprt', 
                'prv_pmnts_corp', 
                'ideal_pmnts_corp', 
                'ideal_pmnts_sprt', 
                'pmnts_2_sprt', 
                'slope_subsprt', 
                'subsprt_info', 
                'slope', 
                'slack', 
                'sprt_prcp_owed', 
                'ideal_pmnts_sprt_init', 
                'ideal_pmnts_corp_init', 
                'corp_pmnts', 
                'corp_prcp_perPrd', 
                'corp_intr_perPrd', 
                'corp_pnlt_perPrd', 
                'corp_pmnt_current', 
                'corp_intr_owed', 
                'corp_prcp_paid', 
                'corp_intr_paid', 
                'corp_prcp_owed', 
                'sprt_pmnts', 
                'sprt_prcp_perPrd', 
                'sprt_intr_perPrd', 
                'sprt_pnlt_perPrd', 
                'sprt_pmnt_current', 
                'sprt_intr_owed', 
                'sprt_prcp_paid', 
                'sprt_intr_paid', 
                'intercept_sprt', 
                'intercept_corp', 
                'corp_pmnt_perCollect', 
                'corp_prcp_perCollect', 
                'corp_intr_perCollect', 
                'corp_pnlt_perCollect', 
                'sprt_pmnt_perCollect', 
                'sprt_prcp_perCollect', 
                'sprt_intr_perCollect', 
                'sprt_pnlt_perCollect', 
                'corp_collect_current', 
                'sprt_collect_current', 
                'corp_collect_full_repay', 
                'sprt_collect_full_repay']
    
    def __init__(self,
        prcp_corp: float,
        prcp_sprt: float,
        APR_corp: float,
        APR_sprt: float,
        loan_tnr: float,
        prv_pmnts_corp: List[float]=[],
        prv_pmnts_sprt: List[float]=[],
        subsprt_info: Any={},
        APR_pnlt: float=0,
        max_slope: float=np.inf,
        annual_cmpnd_prds: int=12,
        collection_freq: int=1,
        collection_dates: List[dt.datetime] = [],
        sig_figs_2rnd: int = DEFAULT_PRECISION_MONEY,
        tol: float = 10**(-DEFAULT_PRECISION_MONEY-1),
        num_CPUs: int = 1):
        
        """
        calculates payment per period for two interlinked tranches (e.g. supporter, corpus)
        such that payments linearly increase for the junior tranche and linearly
        decrease for the senior tranche. Also deals with all idiosyncracies regarding dates, late-payments, 
        adjusting payments for over/under payment, etc -- this is the "brains" of the Loan
    
        Parameters
        ----------
        prcp_corp   (float): principal committed by corpus (senior tranche)
        prcp_sprt   (float): principal committed by supporter (junior tranche)
        APR_corp    (float): annual percentage rate for corpus 
        APR_sprt    (float): annual percentage rate for supporter 
        loan_tnr    (float): loan tenure in terms of collection periods (if partial period can be e.g. 6.4)
        prv_pmnts_corp (List[float]): all previous payments to the corpus tranche
        prv_pmnts_sprt (List[float]): all previous payments to the supporter tranche
        subsprt_info (Dict): if there are more than 2 tranches then this code runs bottom up on each pair
                             the bottom two (most junior) tranches are first run together
                             then the senior tranche from above is run with its more senior tranche
                             i.e. the corpus in the first pair becomes the supporter in the second
                             but needs the following info from the junior tranche (original supporter) as a dict
                             'pmnts_2_sprt': all payments the "middle" tranche receives from the junior tranche
                             'slope_subsprt': slope of the junior tranche payments
        APR_pnlt    (float): annual interest rate on late payments
        max_slope   (float): max allowable slope (can set to 0 if want vanilla schedule)
        coupon_type   (str): right now only "tranched" works but can add "credit-line" and others in future
        annual_cmpnd_prds (int): number of interest-rate periods per year (e.g. 12=monthly)
        collection_freq (int): number compounding periods per collection (e.g. 30 if daily compounding and monthly collection)
        sig_figs_2rnd (int): number of significant figures to round (depends on currency)
        num_CPUs      (int): can run faster if parallelized
        tol         (float): value below which discrepancies in payments will be rounded to 0
    
        Returns: Coupon Object with following attributes
        ---------------------------------------
        corp_pmnt_current (float): current amount to pay to corpus tranche
        sprt_pmnt_current (float): current amount to pay to supporter tranche
        corp_pmnts       (np.array): all past and future payments for corpus tranche
        sprt_pmnts       (np.array): all past and future payments for supporter tranche
        corp_intr_perPrd (np.array): interest paid per period for all past and future payments for supporter tranche
        sprt_intr_perPrd (np.array): interest paid per period for all past and future payments for corpus tranche
        corp_pnlt_perPrd (np.array): penalty paid per period for all past and future payments for corpus tranche
        sprt_pnlt_perPrd (np.array): penalty paid per period for all past and future payments for supporter tranche
        corp_prcp_perPrd (np.array): principal paid per period for all past and future payments for corpus tranche
        sprt_prcp_perPrd (np.array): principal paid per period for all past and future payments for supporter tranche
        slope          (float): slope value of linear equation describing future payments
        intercept_sprt (float): intercept value of linear equation describing future payments for supporter tranche
        intercept_corp (float): intercept value of linear equation describing future payments for corpus tranche
        """
        
        # assert prv_pmnts len is same
        assert len(prv_pmnts_corp)==len(prv_pmnts_corp), \
               "previous payment vectors of different lengths"
        
        # assert APRs>0 (cause not implemented yet)
        if APR_corp==0 or APR_sprt==0:
          raise NotImplementedError("APRs cannot be 0th for now")
        
        # store basic info
        self.prcp_corp = prcp_corp
        self.prcp_sprt = prcp_sprt
        self.max_slope = max_slope*(loan_tnr>1)
        self.sig_figs_2rnd = sig_figs_2rnd
        self.tol = tol
        self.num_CPUs = num_CPUs
        
        # calc period percentage rate
        self.APR_corp = APR_corp
        self.APR_sprt = APR_sprt
        self.APR_pnlt = APR_pnlt
        self.PPR_corp = APR_corp / annual_cmpnd_prds  
        self.PPR_sprt = APR_sprt / annual_cmpnd_prds  
        self.PPR_pnlt = APR_pnlt / annual_cmpnd_prds
        
        # IMPORTANT: for the context of the coupon class what one would typically
        # define as a "Payment" is a "Collection" as it is unitized by collection frequency
        # the collection frequency is ALWAYS >= compounding frequency (i.e. min value is 1)
        self.prv_collect_sprt = np.array(prv_pmnts_sprt)
        self.prv_collect_corp = np.array(prv_pmnts_corp)
        
        # convert units -- loan_tnr must be in terms of compounding periods
        self.num_prv_collect = len(prv_pmnts_corp)
        self.num_tot_collect = np.ceil(loan_tnr).astype(int)
        loan_tnr = loan_tnr * collection_freq

        # get first period length
        self.days_per_period = np.round(360/annual_cmpnd_prds)
        fst_prd_len = (np.round(loan_tnr * collection_freq * self.days_per_period)/self.days_per_period) % 1
        if fst_prd_len == 0:
            fst_prd_len = 1
        loan_tnr = np.ceil(loan_tnr).astype(int)
        self.loan_tnr = loan_tnr
        self.loan_tnr_orig = copy.copy(self.loan_tnr)
        self.fst_prd_len = fst_prd_len

        # store other time related info
        self.annual_cmpnd_prds = annual_cmpnd_prds
        self.collection_freq = collection_freq
        
        # map compounding periods to collection periods
        if bool(collection_dates):
            assert(len(collection_dates)) == self.loan_tnr
            self.start_date = collection_dates[0]
            self.indx_prd_2_collect = [int(np.floor((date-collection_dates[0]).days/self.days_per_period)) \
                                            for date in collection_dates[1:]]
        else:
            self.indx_prd_2_collect = np.arange(loan_tnr % collection_freq,
                                                loan_tnr+1, collection_freq)
        self.indx_prd_2_collect = np.pad(self.indx_prd_2_collect[self.indx_prd_2_collect>0],(1,0))
        self.num_prv_pmnts = self.indx_prd_2_collect[self.num_prv_collect]

        # combine collection info into a dictionary
        self.collection_dict = {prd:(None,None) for prd in self.indx_prd_2_collect}
        self.collection_dict[self.indx_prd_2_collect[0]] = tuple((0,0))
        for i in range(0,self.num_prv_collect):
            self.collection_dict[self.indx_prd_2_collect[i+1]] = (self.prv_collect_corp[i],self.prv_collect_sprt[i])
        
        # IMPORTANT: for the context of the coupon class "Payments" are unitized by the 
        # compounding freqeuncy (annual_cmpnd_prds) which defines a unit of one period
        # ergo collections are broken into payments (e.g. monthly collection to daily payments)
        self.prv_pmnts_sprt = np.full(self.num_prv_pmnts, np.NaN)
        self.prv_pmnts_corp = np.full(self.num_prv_pmnts, np.NaN)        
        
        # vectors storing ideal past/future payments
        self.ideal_pmnts_corp = np.full(self.loan_tnr, np.NaN)
        self.ideal_pmnts_sprt = np.full(self.loan_tnr, np.NaN)
        
        # parse sub-supporter info if present
        if bool(subsprt_info):
            self.pmnts_2_sprt = subsprt_info['pmnts_2_sprt']
            self.slope_subsprt = subsprt_info['slope_subsprt']
        else:
            self.pmnts_2_sprt = []
            self.slope_subsprt = 0
        self.subsprt_info = subsprt_info
        
        # starting values for function below
        self.slope = None
        self.slack = 0
        self.sprt_prcp_owed = copy.copy(prcp_sprt)
        
        # if coupon_type=='tranched':
        self.calc_tranche_coupon()
    
    def _calc_eqn_matrices(self,
        prv_pmnts_corp=[],
        prv_pmnts_sprt=[],
        ideal_pmnts_corp=[],
        ideal_pmnts_sprt=[]):
        """
        core math logic - computes the matrices which when linearly equated the
        solution yields the amount each tranche is paid per period

        Parameters
        ----------
        prv_pmnts_corp (List[float]): all previous payments to the corpus tranche
        prv_pmnts_sprt (List[float]): all previous payments to the supporter tranche
        ideal_pmnts_corp (List[float]): what should have been the payment to the corpus each period
        ideal_pmnts_sprt (List[float]): same as above for supporter, vectors computed at first instantiation

        Returns (think linear eqn: y = intercept+x*slope)
        -------
        LHS_mtx, RHS_mtx, intercept_coef_mtx, slope_coef_mtx
        """
        
        fst_prd_len = self.fst_prd_len
        prcp_sprt = self.prcp_sprt
        prcp_corp = self.prcp_corp
        PPR_sprt = self.PPR_sprt
        PPR_corp = self.PPR_corp
        PPR_pnlt = self.PPR_pnlt
        loan_tnr = self.loan_tnr
        tol = self.tol
        
        k = len(prv_pmnts_corp)
        # compute accrued interest as to subtract previous payments from LHS
        if k>0:
            # normalize first period by fst_prd_len
            prv_pmnts_sprt[0]   =   prv_pmnts_sprt[0]/fst_prd_len
            prv_pmnts_corp[0]   =   prv_pmnts_corp[0]/fst_prd_len
            ideal_pmnts_sprt[0] = ideal_pmnts_sprt[0]/fst_prd_len
            ideal_pmnts_corp[0] = ideal_pmnts_corp[0]/fst_prd_len
        
            # subtract penalties from previous payments
            penalty_sprt = np.maximum(0, ideal_pmnts_sprt[0:k] - prv_pmnts_sprt) * PPR_pnlt
            penalty_corp = np.maximum(0, ideal_pmnts_corp[0:k] - prv_pmnts_corp) * PPR_pnlt
            penalty_sprt[penalty_sprt<=tol*10] = 0
            penalty_corp[penalty_corp<=tol*10] = 0
        
            # previous payments must discounted by the interest owed
            prv_intr_sprt = np.array([(1+PPR_sprt)**(loan_tnr-t) for t in np.arange(1,k+1)])
            prv_intr_sprt[0] = (1+PPR_sprt)**(loan_tnr-fst_prd_len)
            prv_intr_corp = np.array([(1+PPR_corp)**(loan_tnr-t) for t in np.arange(1,k+1)])
            prv_intr_corp[0] = (1+PPR_corp)**(loan_tnr-fst_prd_len) 

            # reinstate scaling first period by fst_prd_len
            prv_pmnts_sprt[0]   =   prv_pmnts_sprt[0]*fst_prd_len
            prv_pmnts_corp[0]   =   prv_pmnts_corp[0]*fst_prd_len
            ideal_pmnts_sprt[0] = ideal_pmnts_sprt[0]*fst_prd_len
            ideal_pmnts_corp[0] = ideal_pmnts_corp[0]*fst_prd_len           
        else:
            prv_intr_sprt = []
            prv_intr_corp = []
            penalty_sprt = 0
            penalty_corp = 0
        
        # compute left hand side of equations
        ## need to deal with numerical instability (via tol)
        LHS_sprt = prcp_sprt*(1+PPR_sprt)**(loan_tnr-1)*(1+fst_prd_len*PPR_sprt) \
                   - np.dot(prv_pmnts_sprt-penalty_sprt,prv_intr_sprt)
        LHS_sprt = LHS_sprt*(LHS_sprt>tol)           
        LHS_corp = prcp_corp*(1+PPR_corp)**(loan_tnr-1)*(1+fst_prd_len*PPR_corp) \
                   - np.dot(prv_pmnts_corp-penalty_corp,prv_intr_corp) 
        LHS_corp = LHS_corp*(LHS_corp>tol)
        
        # compute coefficients (if k>0 then first payment already included in LHS)
        coef_intercept_sprt = fst_prd_len*(1+PPR_sprt)**(loan_tnr-1)*(k==0) \
                              + ((1+PPR_sprt)**(loan_tnr-max(k,1))-1)/PPR_sprt
        coef_intercept_corp = fst_prd_len*(1+PPR_corp)**(loan_tnr-1)*(k==0) \
                              + ((1+PPR_corp)**(loan_tnr-max(k,1))-1)/PPR_corp
        coef_intercept_sprt = max(0,coef_intercept_sprt)
        coef_intercept_corp = max(0,coef_intercept_corp)
        
        #coef_slope_sprt = ((PPR_sprt+1)**(loan_tnr-k)-loan_tnr*PPR_sprt-1)/(PPR_sprt**2)
        coef_slope_sprt = sum([(i-1)*(1+PPR_sprt)**(loan_tnr-i) for i in np.arange(1,loan_tnr+1)][k:])
        #coef_slope_corp = ((PPR_corp+1)**(loan_tnr-k)-loan_tnr*PPR_corp-1)/(PPR_corp**2)
        coef_slope_corp = sum([(i-1)*(1+PPR_corp)**(loan_tnr-i) for i in np.arange(1,loan_tnr+1)][k:])
                
        # assemble values into matrices
        LHS_mtx = np.array([LHS_sprt,LHS_corp])
        intercept_coef_mtx = np.array([[coef_intercept_sprt,0],[0,coef_intercept_corp]])
        slope_coef_mtx = np.array([coef_slope_sprt,-coef_slope_corp])
        # below matrix only used if subtranches
        RHS_mtx = np.array([[coef_intercept_sprt,coef_slope_sprt],
                            [-coef_intercept_corp,-coef_slope_corp]])
        
        return LHS_mtx, RHS_mtx, intercept_coef_mtx, slope_coef_mtx
    
    def _create_soln_functions(self,
        prv_pmnts_corp,
        prv_pmnts_sprt,
        ideal_pmnts_corp,
        ideal_pmnts_sprt):
        """
        core math logic - we have a 3 variable, 2 equation system. Ergo, setting any one 
        variable allows us to solve the others through simple matrix inversion

        Parameters
        ----------
        prv_pmnts_corp (List[float]): all previous payments to the corpus tranche
        prv_pmnts_sprt (List[float]): all previous payments to the supporter tranche
        ideal_pmnts_corp (List[float]): what should have been the payment to the corpus each period
        ideal_pmnts_sprt (List[float]): same as above for supporter, vectors computed at first instantiation

        Returns 
        -------
        function that return the solution matrix given a particular variable
        solution matrix always have following form: [intercept supporter, intercept corpus, slope]
        """
        
        k = len(prv_pmnts_corp)

        loan_tnr = self.loan_tnr
        pmnts_2_sprt = self.pmnts_2_sprt
        slope_subsprt = self.slope_subsprt
        
        # do the math
        LHS_mtx, RHS_mtx, intercept_coef_mtx, slope_coef_mtx = \
            self._calc_eqn_matrices(prv_pmnts_corp,
                                    prv_pmnts_sprt,
                                    ideal_pmnts_corp,
                                    ideal_pmnts_sprt)
        
        coef_slope_sprt = RHS_mtx[0,1]
        coef_slope_corp = -RHS_mtx[1,1]
        LHS_sprt = LHS_mtx[0]
        LHS_corp = LHS_mtx[1]
        coef_intercept_corp = intercept_coef_mtx[1,1]
        coef_intercept_sprt = intercept_coef_mtx[0,0]
        
        # used for optimization with max_intercept dist
        def calc_soln_from_slope(slope):
            soln_mtx = np.linalg.solve(intercept_coef_mtx,
                                    LHS_mtx-slope*slope_coef_mtx)
        
            # structure of solution matrix:
            #intercept_sprt = soln_mtx[0]
            #intercept_corp = soln_mtx[1]
            
            return np.append(soln_mtx,slope)
        
        # used to compute solution from slack
        def calc_soln_from_slack(slack):
            intercept_subsprt = pmnts_2_sprt[max(k-1,0)]-slack
            
            LHS_mtx = np.array([LHS_sprt+coef_slope_sprt*slope_subsprt,
                                LHS_corp-coef_intercept_corp*intercept_subsprt])         
            soln_mtx = np.linalg.solve(RHS_mtx,LHS_mtx)
            
            intercept_corp = intercept_subsprt-soln_mtx[0]
            
            return np.array([soln_mtx[0],intercept_corp,soln_mtx[1]])
        
        # compute max possible value of slope (linear eqn: payment = intercept+t*slope) 
        # by setting intercept_sprt=1
        def solve_slope_from_intercept(min_intercept_sprt):
            LHS_mtx = np.array([LHS_sprt-min_intercept_sprt*coef_intercept_sprt,
                                LHS_corp])
            RHS_mtx = np.array([[0,coef_slope_sprt],
                                [coef_intercept_corp,-coef_slope_corp]])
            try:
                soln_mtx = np.linalg.solve(RHS_mtx,LHS_mtx)
            except Exception as e:
                soln_mtx = np.linalg.lstsq(RHS_mtx,LHS_mtx)
            return soln_mtx[1], soln_mtx[0] # slope, intercept
        
        return calc_soln_from_slope, calc_soln_from_slack, solve_slope_from_intercept, intercept_coef_mtx 
            
    def _optim_slope(self, k, max_slope, min_slope, calc_soln_from_slope):
        """
        optimization logic - the slope variable is the slope with which supporter payments
        rise and corpus payments fall, optimizer chooses it to be as steep as possible while
        satisfying constraints

        Parameters
        ----------
        k (int): time period
        max_slope (float): maximum allowed for this parameter (needed by optimizer)
        min_slope (float): minimum allowed for this parameter (needed by optimizer)
        calc_soln_from_sope (function): function returning solution matrix from slope variable

        Returns 
        -------
        optimized slope parameter
        """

        loan_tnr = self.loan_tnr
                
        # define optimization functions
        def max_intercept_dist(slope):
            soln_mtx = calc_soln_from_slope(slope[0])
            intercept_sprt = soln_mtx[0]
            intercept_corp = soln_mtx[1]
            
            return -1*(intercept_corp-intercept_sprt)
        
        # set constraints (intercepts > 0) - ideally we want to linearize
        def ensure_positive_intercepts(slope):
            return calc_soln_from_slope(slope[0])
        
        nlc1 = optimize.NonlinearConstraint(ensure_positive_intercepts,0,np.inf)
        #np.ceil(max_intercept_corp-min_intercept_sprt))
        
        # set constraints (all payments > 0) - ideally we want to linearize
        def ensure_positive_payments1(slope):
            soln_mtx = calc_soln_from_slope(slope[0])
            intercept_sprt = soln_mtx[0]
            intercept_corp = soln_mtx[1]
            
            # compute payments
            pmnt_sprt = intercept_sprt + slope*np.arange(k,loan_tnr)
            pmnt_corp = intercept_corp - slope*np.arange(k,loan_tnr)
            
            # filter negative payments
            # pmnt_sprt = list(filter(lambda x: x<0,pmnt_sprt))
            # pmnt_corp = list(filter(lambda x: x<0,pmnt_corp))
            #np.nansum(pmnt_sprt)+np.nansum(pmnt_corp)
            return np.append(pmnt_sprt,pmnt_corp)
        
        nlc2 = optimize.NonlinearConstraint(ensure_positive_payments1,0,np.inf)
            
        rslt = optimize.differential_evolution(max_intercept_dist,
                                               bounds=[(min_slope,min(self.max_slope,max_slope))],
                                               constraints = (nlc1,nlc2),
                                               workers = self.num_CPUs)
        slope = rslt.x[0]
        
        return slope
    
    def _optim_slack(self, k, calc_soln_from_slack):
        """
        optimization logic - the slack variable emerges when we have more than two tranches
        i.e. senior corpus -> junior corpus -> supporter. The slack variable is needed to 
        compute the parameters between the senior and junior corpus at which debt is novated

        Parameters
        ----------
        k (int): time period
        calc_soln_from_slack (function): function returning solution matrix from slack variable

        Returns 
        -------
        optimized slack parameter
        """
        
        loan_tnr = self.loan_tnr
        pmnts_2_sprt = self.pmnts_2_sprt
                
        # used when solving with multiple tranches (need a slack variable)
        def min_slack(slack):
            return np.abs(slack[0])
                
        # ensure positive parameters
        def ensure_positive_params(slack):
            return calc_soln_from_slack(slack[0])
        
        nlc3 = optimize.NonlinearConstraint(ensure_positive_params,0,np.inf)
        
        # ensure positive payments
        def ensure_positive_payments2(slack):         
            soln_mtx = calc_soln_from_slack(slack[0])
            
            slope = soln_mtx[2]
            intercept_sprt = soln_mtx[0]
            intercept_corp = soln_mtx[1]
            
            # compute payments
            pmnt_corp = intercept_corp-np.arange(k,loan_tnr)*slope
            pmnt_sprt = pmnts_2_sprt-pmnt_corp
            
            # filter negative payments
            #pmnt_sprt = list(filter(lambda x: x<0,pmnt_sprt))
            #pmnt_corp = list(filter(lambda x: x<0,pmnt_corp))
        
            return np.append(pmnt_corp,pmnt_sprt)
        
        nlc4 = optimize.NonlinearConstraint(ensure_positive_payments2,0,np.inf)
        
        rslt = optimize.differential_evolution(min_slack,
                                               bounds=[(0,self.prcp_corp)],
                                               constraints = (nlc3,nlc4),
                                               workers = self.num_CPUs)
        
        slack = rslt.x[0]
        
        return slack
        
    def _calc_tranche_pmnts(self,
        prv_pmnts_corp=[],
        prv_pmnts_sprt=[],
        ideal_pmnts_corp=[],
        ideal_pmnts_sprt=[],
        ideal_slope=None,
        ideal_slack=0):
        """
        core payment calculation logic - all functions above utilized by this function
        checks if actual payments matches the ideal payments
        --> if not then updates future payments, else returns ideal payments

        Parameters
        ----------
        prv_pmnts_corp (List[float]): all previous payments to the corpus tranche
        prv_pmnts_sprt (List[float]): all previous payments to the supporter tranche
        ideal_pmnts_corp (List[float]): what should have been the payment to the corpus each period
        ideal_pmnts_sprt (List[float]): same as above for supporter, vectors computed at first instantiation
        ideal_slope (float): slope variable computed prior to new payments
        ideal_slack (float): slack variable computed prior to new payments (if more than 2 tranches)

        Returns 
        -------
        pmnt_sprt (np.array): past and expecture future payments to supporter
        pmnt_corp (np.array): past and expecture future payments to corpus
        slope (float): updated slope variable (shared by both corpus and supporter)
        intercept_sprt (float): updated intercept variable for supporter
        intercept_corp (float): updated intercept variable for corpus
        slack (float): update slack variable (if more than 2 tranches)
        """
        
        loan_tnr = self.loan_tnr
        pmnts_2_sprt = self.pmnts_2_sprt
        fst_prd_len = self.fst_prd_len
        tol = self.tol
        k = len(prv_pmnts_corp)
        
        # payments have occurred
        if k>0:
            # payments are ideal
            if np.abs((ideal_pmnts_corp[k-1]+ideal_pmnts_sprt[k-1]) \
                      -(prv_pmnts_corp[k-1]+prv_pmnts_sprt[k-1]))<tol:
                # next payments are computed
                if not np.isnan(ideal_pmnts_sprt[k]) and not np.isnan(ideal_pmnts_corp[k]):
                    # no need to compute anything new -- regurgitate original calculations
                    return np.append(prv_pmnts_sprt,ideal_pmnts_sprt[k:]), \
                           np.append(prv_pmnts_corp,ideal_pmnts_corp[k:]), \
                           ideal_slope, \
                           None, \
                           None, \
                           ideal_slack

        # retrieve solution functions
        calc_soln_from_slope, calc_soln_from_slack, solve_slope_from_intercept, intercept_coef_mtx = \
            self._create_soln_functions(prv_pmnts_corp,
                                   prv_pmnts_sprt,
                                   ideal_pmnts_corp,
                                   ideal_pmnts_sprt)
        
        # determine if we need to run optimizer or not
        slack = 0
        min_slope = 0
        
        ## slope is hardset to 0 or it is the last run
        if self.max_slope==0 or k>=(loan_tnr-1):
            max_slope = ideal_slope = 0
        ## first run so nothing computed as of yet (must compute)
        elif k==0 or ideal_slope is None:
            min_intercept_sprt = max(self.PPR_sprt*self.sprt_prcp_owed,1)
            max_slope, max_intercept_corp = solve_slope_from_intercept(min_intercept_sprt)
        ## payments have occurred 
        else:
            ## payments less than ideal
            if (ideal_pmnts_corp[k-1]+ideal_pmnts_sprt[k-1])>(prv_pmnts_corp[k-1]+prv_pmnts_sprt[k-1]):
                min_intercept_sprt = max(self.PPR_sprt*self.sprt_prcp_owed,ideal_pmnts_sprt[max(0,k-2)])
                max_slope, max_intercept_corp = solve_slope_from_intercept(min_intercept_sprt)
                min_slope = ideal_slope*(ideal_slope<max_slope)
            ## payments more than ideal
            elif (ideal_pmnts_corp[k-1]+ideal_pmnts_sprt[k-1])<(prv_pmnts_corp[k-1]+prv_pmnts_sprt[k-1]):
                min_intercept_sprt = max(self.PPR_sprt*self.sprt_prcp_owed,ideal_pmnts_sprt[max(0,k-1)])
                max_slope, max_intercept_corp = solve_slope_from_intercept(min_intercept_sprt) 
        
        # run 
        max_slope = max(0,max_slope)
        if min_slope!=max_slope:
            if bool(self.subsprt_info): # if subsupporter
                slack = self._optim_slack(k,calc_soln_from_slack)
            else:
                slope = self._optim_slope(k,max_slope,min_slope,calc_soln_from_slope)
        else:
            slope = min(max_slope,ideal_slope)
            slack = ideal_slack

        if bool(self.subsprt_info): # if subsupporter
            soln_mtx = calc_soln_from_slack(slack)
        else:
            if np.count_nonzero(intercept_coef_mtx)>0:
                soln_mtx = calc_soln_from_slope(slope)
            else:
                soln_mtx = np.zeros(2)

        # retrieve optimal values
        intercept_sprt = soln_mtx[0]
        intercept_corp = soln_mtx[1]
        slope = soln_mtx[2]
        
        # compute payments
        pmnt_corp = intercept_corp - slope*np.arange(k,loan_tnr)
        if bool(self.subsprt_info):
            pmnt_sprt = pmnts_2_sprt - pmnt_corp
        else:
            pmnt_sprt = intercept_sprt + slope*np.arange(k,loan_tnr)
        
        # once again adjust first period length
        if k==0:
          pmnt_sprt[0] = pmnt_sprt[0]*fst_prd_len
          pmnt_corp[0] = pmnt_corp[0]*fst_prd_len
        
        # append payments
        pmnt_sprt = np.append(prv_pmnts_sprt,pmnt_sprt)
        pmnt_corp = np.append(prv_pmnts_corp,pmnt_corp)
                
        return pmnt_sprt, pmnt_corp, slope, intercept_sprt, intercept_corp, slack
    
    def _calc_prcp_intr_pnlt(self,pmnt_vec,PPR,principal,ideal_pmnt_vec):
        """
        from the payment vector, parses how much is return to principal, interest, or penalty

        Parameters
        ----------
        pmnt_vec (np.array): all past and future expected payments
        PPR (float): period percentage rate
        principal (float): principal lent out by tranche
        ideal_pmnt_vec (np.array): see above

        Returns 
        -------
        intr_perPrd (np.array): interest paid per period
        prcp_perPrd (np.array): return to principal per period
        pnlt_perPrd (np.array): penalty paid per period
        """
        
        intr_perPrd = np.zeros(self.loan_tnr)
        prcp_perPrd = np.zeros(self.loan_tnr)
        pnlt_perPrd = np.zeros(self.loan_tnr)
        
        # calculate first period
        intr_perPrd[0] = np.maximum(0,PPR*self.fst_prd_len*principal)
        pnlt_perPrd[0] = np.maximum(0,ideal_pmnt_vec[0]-pmnt_vec[0])*self.PPR_pnlt
        prcp_perPrd[0] = pmnt_vec[0]-intr_perPrd[0]-pnlt_perPrd[0]
        
        # calculate remaining in for loop
        for i in range(1, self.loan_tnr):
            # interest per period
            intr_perPrd[i] = np.maximum(0,(principal-np.sum(prcp_perPrd[0:i])))*PPR
            # penalty per period
            pnlt_perPrd[i] = np.maximum(0,ideal_pmnt_vec[i]-pmnt_vec[i])*self.PPR_pnlt
            # principal per period
            prcp_perPrd[i] = pmnt_vec[i]-intr_perPrd[i]-pnlt_perPrd[i]
            # check if principal and interest negate
            if prcp_perPrd[i]!=0 and intr_perPrd[i]!=0 and \
               np.abs(prcp_perPrd[i]+intr_perPrd[i])<self.tol/10:
                intr_perPrd[i] = 0
                prcp_perPrd[i] = 0
        
        # deal with overpayments (recorded as negative penalties)
        indx = np.searchsorted(np.cumsum(prcp_perPrd),principal)
        if indx<(self.loan_tnr-1):
            original_value = prcp_perPrd[indx].copy()
            prcp_perPrd[indx] = principal-np.sum(prcp_perPrd[0:indx])
            pnlt_perPrd[indx] = prcp_perPrd[indx]-original_value
            
        # 0 out penalties below the tolerance
        pnlt_perPrd[np.abs(pnlt_perPrd)<self.tol*10] = 0

        return prcp_perPrd, intr_perPrd, pnlt_perPrd
   
    def _remove_dangling_cents(self,vec):
        """
        if end of vector has tiny values (100x smaller than the previous val)
        then move it to end-1 and set end to 0
        -->needed because often payments at last period maybe very close to 0
        """
        if np.isnan(vec[-1]):
            vec[-1] = 0
        if len(vec)>1 and np.abs(vec[-1]/vec[-2]) < self.tol*10:
            if (self.loan_tnr-self.num_prv_pmnts)>1:
                vec[-2] += vec[-1]
            vec[-1] = 0
        return vec
    
    def _checksum_payments(self,pmnt_vec,orig_prv_pmnts,prcp_perPrd,intr_perPrd,pnlt_perPrd,principal):
        """
        ensure prcp_perPrd adds up to principal and adjust all other vectors accordingly
        needed as numerically instability means principal payments may add up close to principal
        but not quite

        Parameters
        ----------
        pmnt_vec (np.array): all past and future expected payments
        orig_prv_pmnts (np.array): original previous payment passed in
        prcp_perPrd (np.array): principal per period
        intr_perPrd (np.array): interest per period
        pnlt_perPrd (np.array): penalty per period
        principal (float): principal lent by tranche

        Returns 
        -------
        pmnt_vec (np.array): vector of past and future payments to tranche
        intr_perPrd (np.array): interest paid per period
        prcp_perPrd (np.array): return to principal per period
        pnlt_perPrd (np.array): penalty paid per period  
        """

        # any negative interest needs to be added to principal
        if np.any(intr_perPrd<0):
            prcp_perPrd[intr_perPrd<0] += -intr_perPrd[intr_perPrd<0]
            intr_perPrd[intr_perPrd<0] = 0

        # remove dangling centspny
        if np.any(pmnt_vec<=0):
            intr_perPrd = self._remove_dangling_cents(intr_perPrd)
            prcp_perPrd = self._remove_dangling_cents(prcp_perPrd)

        # if principal doesn't match up slightly (numerical issues remain)
        if prcp_perPrd.sum()!=principal:
            coef = (principal-prcp_perPrd[0:self.num_prv_pmnts].sum()) \
                    / prcp_perPrd[self.num_prv_pmnts:].sum()
            prcp_perPrd[self.num_prv_pmnts:] = prcp_perPrd[self.num_prv_pmnts:]*coef
            prcp_perPrd = np.nan_to_num(prcp_perPrd)

        # finally adjust to ensure interest+principal=payment (arises due to numerical issues)
        pmnt_vec = np.append(orig_prv_pmnts,pmnt_vec[self.num_prv_pmnts:])
        if (self.loan_tnr-self.num_prv_pmnts)>1 or \
           (intr_perPrd[self.num_prv_pmnts]+prcp_perPrd[self.num_prv_pmnts])>pmnt_vec[self.num_prv_pmnts]:
            intr_perPrd = pmnt_vec-prcp_perPrd-np.abs(pnlt_perPrd)
        
        return pmnt_vec, prcp_perPrd, intr_perPrd, pnlt_perPrd
        
    def _collections_2_periods(self,
        ideal_pmnts_sprt,
        ideal_pmnts_corp,
        start_collect=0,
        end_collect=None):
        """
        breaks down prv_pmnts received by collection_freq into payments received by the compounding frequency
        e.g. converting monthly collections to daily payments
        i.e. there is a one to many relationship between collections and payments
        
        Parameters
        ----------
        ideal_pmnts_corp (List[float]): what should have been the payment to the corpus each period
        ideal_pmnts_sprt (List[float]): same as above for supporter, vectors computed at first instantiation
        start_collect: index of which collection to start conversion from
        end_collection: index of which collection to end conversion and
        """
        
        # helper function
        def calc_pmnts_per_collect(collect_amt,ideal_pmnts):
            num_pmnts = len(ideal_pmnts)
            indx = min(np.searchsorted(np.cumsum(ideal_pmnts),collect_amt),num_pmnts-1)
            pmnt_vec = np.pad(ideal_pmnts[0:(indx+1)],(0,(num_pmnts-(indx+1))))
            pmnt_vec[indx] = collect_amt-np.sum(ideal_pmnts[0:indx])
            
            return pmnt_vec
        
        # no need to do anything if collection and compounding freq same
        if self.collection_freq==1:
            self.prv_pmnts_sprt = self.prv_collect_sprt.copy()
            self.prv_pmnts_corp = self.prv_collect_corp.copy()
        else:
        # if there is a difference between frequencies
            if end_collect is None:
                end_collect = self.num_prv_collect
            # core logic
            for i in range(start_collect,min(end_collect,self.num_prv_collect)):
                # get indices
                pmnt_indx_str = self.indx_prd_2_collect[i]
                pmnt_indx_end = self.indx_prd_2_collect[i+1]
                # convert for supporter
                self.prv_pmnts_sprt[pmnt_indx_str:pmnt_indx_end] = \
                    calc_pmnts_per_collect(self.prv_collect_sprt[i],
                                           ideal_pmnts_sprt[pmnt_indx_str:pmnt_indx_end])
                # convert for corpus
                self.prv_pmnts_corp[pmnt_indx_str:pmnt_indx_end] = \
                    calc_pmnts_per_collect(self.prv_collect_corp[i],
                                           ideal_pmnts_corp[pmnt_indx_str:pmnt_indx_end])
    
    def calc_tranche_coupon(self,start_period: int=0):
        """
        core function to be called externally, uses all above functions to produce coupon
        see where it says "return" to understand attributes

        Parameters
        ----------
        start_period (int): at what time period should we start calculations from
        """
        
        # check to invoke coupon zero
        if self.prcp_corp==0 and self.prcp_sprt==0:
            self._coupon_zero()
            return
        
        # retrieve previous values
        ideal_pmnts_corp = self.ideal_pmnts_corp 
        ideal_pmnts_sprt = self.ideal_pmnts_sprt
        slope = self.slope
        slack = self.slack

        # check if coupon will have to be finalized now
        finalize = (self.loan_tnr==self.num_prv_pmnts)*1
        
        for i in range(start_period, min(self.num_prv_pmnts+1,self.loan_tnr+finalize)):
            pmnt_sprt, pmnt_corp, slope, intercept_sprt, intercept_corp, slack = \
                 self._calc_tranche_pmnts(self.prv_pmnts_corp[0:i],
                                          self.prv_pmnts_sprt[0:i],
                                          ideal_pmnts_corp[0:self.loan_tnr],#[0:i],
                                          ideal_pmnts_sprt[0:self.loan_tnr],#[0:i],
                                          ideal_slope = slope,
                                          ideal_slack = slack)
            
            # should this be updated as i? may not be necessary-- to do
            ideal_pmnts_sprt[i:] = pmnt_sprt[i:].copy()
            ideal_pmnts_corp[i:] = pmnt_corp[i:].copy()
            
            # convert the future collections to payments based off of newly computed payments
            if (i in self.indx_prd_2_collect[0:-1]):
                collect_indx = int(i/self.collection_freq)
                self._collections_2_periods(pmnt_sprt,pmnt_corp,collect_indx,collect_indx+1)
                
                if i==0:
                    self.ideal_pmnts_sprt_init = pmnt_sprt.copy()
                    self.ideal_pmnts_corp_init = pmnt_corp.copy()
            
            # need to extend loan tenor to finalize coupon (checks nothing remains)
            if finalize and i==(self.loan_tnr-1):
                self.extend_loan_tnr(1)
                ideal_pmnts_corp = np.pad(ideal_pmnts_corp,(0,1),mode='constant',constant_values=np.nan)
                ideal_pmnts_sprt = np.pad(ideal_pmnts_sprt,(0,1),mode='constant',constant_values=np.nan)
                finalize = False
        
        # small payments in the last period should be moved to the prior period
        pmnt_corp = self._remove_dangling_cents(pmnt_corp)
        pmnt_sprt = self._remove_dangling_cents(pmnt_sprt)
        
        # parse interest, principal, penalty payments
        corp_prcp_perPrd, corp_intr_perPrd, corp_pnlt_perPrd = \
            self._calc_prcp_intr_pnlt(pmnt_corp,
                                      self.PPR_corp,
                                      self.prcp_corp,
                                      ideal_pmnts_corp)
                                  
        sprt_prcp_perPrd, sprt_intr_perPrd, sprt_pnlt_perPrd = \
            self._calc_prcp_intr_pnlt(pmnt_sprt,
                                      self.PPR_sprt,
                                      self.prcp_sprt,
                                      ideal_pmnts_sprt)
        
        # adjust vectors to ensure principal exactly sums to actual principal
        pmnt_corp, corp_prcp_perPrd, corp_intr_perPrd, corp_pnlt_perPrd = \
            self._checksum_payments(pmnt_corp,
                                    self.prv_pmnts_corp,
                                    corp_prcp_perPrd,
                                    corp_intr_perPrd,
                                    corp_pnlt_perPrd,
                                    self.prcp_corp)
            
        pmnt_sprt, sprt_prcp_perPrd, sprt_intr_perPrd, sprt_pnlt_perPrd = \
            self._checksum_payments(pmnt_sprt,
                                    self.prv_pmnts_sprt,
                                    sprt_prcp_perPrd,
                                    sprt_intr_perPrd,
                                    sprt_pnlt_perPrd,
                                    self.prcp_sprt)
        
        # return
        self.corp_pmnts = pmnt_corp
        self.corp_prcp_perPrd = corp_prcp_perPrd
        self.corp_intr_perPrd = corp_intr_perPrd
        self.corp_pnlt_perPrd = corp_pnlt_perPrd

        self.corp_pmnt_current = pmnt_corp[self.num_prv_pmnts]
        self.corp_intr_owed = corp_intr_perPrd[self.num_prv_pmnts:].sum()
        self.corp_prcp_paid = corp_prcp_perPrd[0:self.num_prv_pmnts].sum()
        self.corp_intr_paid = corp_intr_perPrd[0:self.num_prv_pmnts].sum()
        self.corp_prcp_owed = self.prcp_corp - self.corp_prcp_paid

        self.sprt_pmnts = pmnt_sprt
        self.sprt_prcp_perPrd = sprt_prcp_perPrd
        self.sprt_intr_perPrd = sprt_intr_perPrd
        self.sprt_pnlt_perPrd = sprt_pnlt_perPrd

        self.sprt_pmnt_current = pmnt_sprt[self.num_prv_pmnts]
        self.sprt_intr_owed = sprt_intr_perPrd[self.num_prv_pmnts:].sum()
        self.sprt_prcp_paid = sprt_prcp_perPrd[0:self.num_prv_pmnts].sum()
        self.sprt_intr_paid = sprt_intr_perPrd[0:self.num_prv_pmnts].sum()
        self.sprt_prcp_owed = self.prcp_sprt - self.sprt_prcp_paid
        
        self.slope = slope
        self.slack = slack

        self.ideal_pmnts_corp[start_period:] = ideal_pmnts_corp[start_period:]
        self.ideal_pmnts_sprt[start_period:] = ideal_pmnts_sprt[start_period:]
        
        if intercept_sprt is not None:
            self.intercept_sprt = intercept_sprt
        if intercept_corp is not None:
            self.intercept_corp = intercept_corp
        
        # convert compounding periods to collections
        self._periods_2_collections()
    
    def _periods_2_collections(self,vec=None):
        """
        coalesces coupon info computed by the compounding frequency
        into vectors unitized by the collection frequency
        e.g. converting daily payments to monthly collections
        """

        def splitsum(vec):
            if self.collection_freq==1:
                return vec
            else:
                return np.fromiter(map(np.sum,
                                       np.split(vec,self.indx_prd_2_collect[1:-1])),
                                    dtype=np.float)
        
        if vec is not None:
            return splitsum(vec)
        else:
            self.corp_pmnt_perCollect = splitsum(self.corp_pmnts)
            self.corp_prcp_perCollect = splitsum(self.corp_prcp_perPrd)
            self.corp_intr_perCollect = splitsum(self.corp_intr_perPrd)
            self.corp_pnlt_perCollect = splitsum(self.corp_pnlt_perPrd)
 
            self.sprt_pmnt_perCollect = splitsum(self.sprt_pmnts)
            self.sprt_prcp_perCollect = splitsum(self.sprt_prcp_perPrd)
            self.sprt_intr_perCollect = splitsum(self.sprt_intr_perPrd)
            self.sprt_pnlt_perCollect = splitsum(self.sprt_pnlt_perPrd)
            
            self.corp_collect_current = self.corp_pmnt_perCollect[self.num_prv_collect]
            self.sprt_collect_current = self.sprt_pmnt_perCollect[self.num_prv_collect]
            self.corp_collect_full_repay = self.corp_prcp_owed*(1+self.PPR_corp)
            self.sprt_collect_full_repay = self.sprt_prcp_owed*(1+self.PPR_sprt)
            
    def _coupon_zero(self):
        # sets all coupon attributes to zero 
        # (for when principal for both corpus and supporters = 0)

        self.corp_pmnts = \
        self.ideal_pmnts_corp = \
        self.corp_prcp_perPrd = \
        self.corp_intr_perPrd = \
        self.corp_pnlt_perPrd = \
        self.sprt_pmnts = \
        self.ideal_pmnts_sprt = \
        self.sprt_prcp_perPrd = \
        self.sprt_intr_perPrd = \
        self.sprt_pnlt_perPrd = np.zeros(self.loan_tnr)
        
        self.sprt_pmnt_current = \
        self.corp_pmnt_current = \
        self.intercept_sprt = \
        self.intercept_corp = \
        self.slope = \
        self.slack = 0

        # convert compounding periods to collections
        self._periods_2_collections()
    
    def _convert_repayments_representation(self,*args):
        """
        convert from corpus and supporter List[(date,amount)] format variables
        to dict representation {period: (corpus amt, supporter amt)}
        and vise versa
        """

        # helper function
        def convert_repayments_2_dict(repayments):
            # parse payment tuple
            parsed = [list(t) for t in zip(*repayments)]
            dates = parsed[0]
            payments = parsed[1]
            
            # convert dates to index
            date_indx = [int(np.floor((date-self.start_date).days/self.days_per_period)) for date in dates]
            
            #coalesce in case multiple payments in period
            pmnt_date_list = list(zip(date_indx,payments))
            coalesced = [[k, sum(v for _, v in g)] for k, g in groupby(sorted(pmnt_date_list), key = lambda x: x[0])]
            
            return {item[0]:item[1] for item in coalesced}

        if len(args)==1 and isinstance(args[0],dict):
            repayments_dict = args[0]
            collections_corp = [(self.start_date+dt.timedelta(days=key*self.days_per_period),val[0]) \
                                    for key,val in repayments_dict.items()]
            collections_sprt = [(self.start_date+dt.timedelta(days=key*self.days_per_period),val[0]) \
                                    for key,val in repayments_dict.items()]
            
            return collections_corp, collections_sprt

        elif len(args)==2:

            collections_corp = list(args[0])
            collections_sprt = list(args[1])
            # assert lenghts are the same
            assert len(collections_corp) == len(collections_sprt)

            # convert to dict with format {periods from start date: amount}
            if all(isinstance(item, tuple) for item in (collections_corp+collections_sprt)):
                collections_corp = convert_repayments_2_dict(collections_corp)
                collections_sprt = convert_repayments_2_dict(collections_sprt)
            elif all(isinstance(item, float) for item in (collections_corp+collections_sprt)):
                collections_corp = {self.indx_prd_2_collect[i+1]:collections_corp[i] for i in range(0,len(collections_corp))}
                collections_sprt = {self.indx_prd_2_collect[i+1]:collections_sprt[i] for i in range(0,len(collections_sprt))}

            # coalesce corpus and supporter dicts into one
            repayments_dict = {prd: tuple(( collections_corp[prd], collections_sprt[prd] )) \
                                    for prd in collections_corp }
            
            return repayments_dict
    
    def extend_loan_tnr(self,
        collect_prds_2_extend: int,
        new_pnlt_APR: float=None):
        """
        Used when payment is late and must extend loan
        
        Parameters
        ----------
        collect_prds_2_extend (int): number of collection periods to extend
        new_pnlt_APR : penalty APR update for extension

        Returns
        -------
        coupon object with extended loan tenor
        """
        
        # update loan tenor
        self.loan_tnr_orig = copy.copy(self.loan_tnr)
        self.loan_tnr += self.collection_freq*collect_prds_2_extend
        self.num_tot_collect += collect_prds_2_extend

        # map compounding periods to collection periods
        new_collection_prds = np.arange(self.collection_freq,
                                        self.collection_freq*collect_prds_2_extend+1,
                                        self.collection_freq)+self.loan_tnr_orig
        self.indx_prd_2_collect = np.append(self.indx_prd_2_collect,new_collection_prds)
        
        # update collection dict
        for prd in new_collection_prds:
            self.collection_dict[prd] = (None,None)

        # vectors storing ideal past/future payments
        self.ideal_pmnts_corp = np.pad(self.ideal_pmnts_corp,
                                       (0,self.loan_tnr -len(self.ideal_pmnts_corp)),
                                         mode='constant', constant_values=np.nan)
        self.ideal_pmnts_sprt = np.pad(self.ideal_pmnts_sprt,
                                       (0,self.loan_tnr -len(self.ideal_pmnts_sprt)),
                                         mode='constant', constant_values=np.nan)
        
        # forces recomputation at next iteration
        # self.ideal_slope = None
   
    def update(self,
        collections_corp: List=[],
        collections_sprt: List=[]):
        """
        instead of reinitializing coupon object, object can be updated
        with new payments as they come in

        Parameters
        ----------
        collections_corp (List[Repayment]): all previous collections into the corpus tranche
        collections_sprt (List[Repayment]): all previous collections into the supporter tranche

        this also works just being called with List[float] instead of repayment class
        """

        # convert collections to single dict representation
        repayments_dict = self._convert_repayments_representation(collections_corp,collections_sprt)
        
        # combine with existing collections_dict
        combined = {**self.collection_dict,**repayments_dict}

        # remove extraneous keys
        dates = sorted(combined.keys())
        ## last non-None entry
        end_indx = np.where([combined[date][0] is not None for date in reversed(dates)])[0][0]
        end_date = list(reversed(dates))[end_indx]
        ## remove
        selected = [date for date in dates if date<end_date and combined[date][0] is None]
        for key in selected:
            combined.pop(key, None)

        # check coalesced dict against the original in memory
        combined = set(sorted(combined.items(),key=lambda x: x[0]))
        diff_items = combined.difference(set(self.collection_dict.items()))
        
        # return which periods are different
        prd_diff = [prd for prd, item in enumerate(sorted(combined,key = lambda x: x[0])) \
                        if item in diff_items]

        if bool(prd_diff):
            
            prd_start = min(prd_diff)
            prd_end = max([key for key,val in combined if val[0] is not None])
            self.num_prv_pmnts = prd_end # bad naming, should be number of payments completed

            # set non-payments to 0 if present, set collection_dict
            keys_2_change = [key for key,val in combined if val[0] is None and key<=prd_end]
            self.collection_dict = dict(sorted(combined,key=lambda x: x[0]))
            self.indx_prd_2_collect = np.array(sorted(self.collection_dict.keys()))
            for key in keys_2_change:
                self.collection_dict[key] = (0,0)

            # update
            self.prv_collect_corp = np.array([val[0] for key,val in self.collection_dict.items() \
                                                     if key<=prd_end and key>0])
            self.prv_collect_sprt = np.array([val[1] for key,val in self.collection_dict.items() \
                                                     if key<=prd_end and key>0])
            self.num_prv_collect = len(self.prv_collect_corp)
            self.num_tot_collect = len(self.indx_prd_2_collect)-1

            # update number of payments finished
            indx = max(0,np.where(self.indx_prd_2_collect==prd_start)[0][0]-1)
            num_pmnts_finished = self.indx_prd_2_collect[indx]
            #self.indx_prd_2_collect[max(0,self.num_prv_collect-1)] #this is not correct

            # delete prv_pmnts values if necessary
            if num_pmnts_finished < len(self.prv_pmnts_corp):
                self.prv_pmnts_corp = self.prv_pmnts_corp[0:num_pmnts_finished]
                self.prv_pmnts_sprt = self.prv_pmnts_sprt[0:num_pmnts_finished]

            # extend loan tenor if necessary
            if self.num_prv_collect>=self.num_tot_collect:
                self.extend_loan_tnr(self.num_prv_collect-self.num_tot_collect+1)
            
            # append to payments
            self.prv_pmnts_corp = np.pad(self.prv_pmnts_corp,
                                         (0,self.num_prv_pmnts -len(self.prv_pmnts_corp)),
                                         mode='constant', constant_values=np.nan)
            self.prv_pmnts_sprt = np.pad(self.prv_pmnts_sprt,
                                         (0,self.num_prv_pmnts -len(self.prv_pmnts_sprt)),
                                         mode='constant', constant_values=np.nan)
            
            # invoke main function
            if np.isnan(self.prv_pmnts_corp[-1]):
                start_period = np.isnan(self.prv_pmnts_corp).nonzero()[0][0]
            else:
                start_period = self.indx_prd_2_collect[self.num_prv_collect]

            self.calc_tranche_coupon(start_period=start_period)
    
    def _update_pmnts_byPrd(self,
        pmnts_perPrd_corp: List=[],
        pmnts_perPrd_sprt: List=[],
        indx_prd_2_collect: List=[],
        set_ideal=False):
        """
        for the credit-line we have to update by compounding period instead of by collections
        this method should never be used otherwise
        """
        def splitsum(vec):
            if self.collection_freq==1:
                return vec
            else:
                return np.fromiter(map(np.sum,
                                       np.split(vec,self.indx_prd_2_collect[1:-1])),
                                    dtype=np.float)

        # basic assertions
        assert len(pmnts_perPrd_corp)==len(pmnts_perPrd_corp)
        self.num_prv_pmnts = len(pmnts_perPrd_corp)

        # replace
        if len(indx_prd_2_collect)>0:
            self.indx_prd_2_collect = indx_prd_2_collect

        # update mapping between colletions and payments by period
        self.num_prv_collect = np.where(self.indx_prd_2_collect<=self.num_prv_pmnts)[0][-1]
        self.prv_collect_corp = splitsum(pmnts_perPrd_corp)[0: self.num_prv_collect]
        self.prv_collect_sprt = splitsum(pmnts_perPrd_sprt)[0: self.num_prv_collect]

        # update collections dict
        collection_dict = self._convert_repayments_representation(self.prv_collect_corp,self.prv_collect_sprt)
        combined = {**self.collection_dict,**collection_dict}

        # remove extraneous keys
        dates = sorted(combined.keys())
        ## last non-None entry
        end_indx = np.where([combined[date][0] is not None for date in reversed(dates)])[0][0]
        end_date = list(reversed(dates))[end_indx]
        ## remove
        selected = [date for date in dates if date<end_date and combined[date][0] is None]
        for key in selected:
            combined.pop(key, None)

        self.collection_dict = combined #dict(sorted(combined,key=lambda x: x[0]))

        # extend loan tenor if necessary
        if self.num_prv_collect>=self.num_tot_collect:
            self.extend_loan_tnr(self.num_prv_collect-self.num_tot_collect+1)
        num_nxt_pmnts = self.indx_prd_2_collect[self.num_prv_collect+1]

        # update vectors with payments by period
        self.prv_pmnts_corp = np.pad(pmnts_perPrd_corp,
                                     (0, num_nxt_pmnts-len(pmnts_perPrd_corp)),
                                     mode='constant', constant_values=np.nan)
        self.prv_pmnts_sprt = np.pad(pmnts_perPrd_sprt,
                                     (0, num_nxt_pmnts-len(pmnts_perPrd_sprt)),
                                     mode='constant', constant_values=np.nan)
        # if set ideal
        if set_ideal:
            self.ideal_pmnts_corp[0:len(pmnts_perPrd_corp)] = pmnts_perPrd_corp.copy()
            self.ideal_pmnts_sprt[0:len(pmnts_perPrd_sprt)] = pmnts_perPrd_sprt.copy()

        # invoke main function
        if np.isnan(self.prv_pmnts_corp[-1]):
            start_period = np.isnan(self.prv_pmnts_corp).nonzero()[0][0]
        else:
            start_period = self.indx_prd_2_collect[self.num_prv_collect]

        self.calc_tranche_coupon(start_period=start_period)
        
    def fetch_repayment_amount(self,repayment_date,full_repay = False):
        """
        get the repayment amount for a particular date
        helpful when the date is between collection dates

        Parameters
        ----------
        repayment_date: either dt.datetim of number of periods since start date

        Returns
        -------
        amount to be repaid to corpus, amount to be repaid to supporter
        """

        # convert date to period
        if isinstance(repayment_date,dt.datetime):
            period = int(np.floor((repayment_date-self.start_date).days/self.days_per_period))
        elif np.issubdtype(type(repayment_date), np.integer):
            period = repayment_date
        else:
            assert False, "Invalid repayment date argument"
        
        # fetch from collections if possible
        if period in self.collection_dict.keys():
            # appopriate repayment
            indx = np.where(self.indx_prd_2_collect==period)[0][0]-1
            if full_repay:
                corp_owed = self.corp_prcp_perPrd[indx:].sum()*(1+self.PPR_corp)
                sprt_owed = self.sprt_prcp_perPrd[indx:].sum()*(1+self.PPR_sprt)
            else:
                corp_owed = self.corp_pmnt_perCollect[indx]
                sprt_owed = self.sprt_pmnt_perCollect[indx]
        else:
            # previous collection (find the ones the period is in between)
            prv_collect_indx = np.where(self.indx_prd_2_collect<period)[0][-1]
            prv_collect_prd = self.indx_prd_2_collect[prv_collect_indx]
            # next collection
            nxt_collect_indx = np.where(self.indx_prd_2_collect>period)[0][0]
            
            # if last repayment
            if period > self.indx_prd_2_collect[-2] or full_repay:
                corp_owed = self.corp_prcp_owed
                sprt_owed = self.sprt_prcp_owed                     
            # in between payment
            else:
                # principal from the next collection
                corp_owed = self.corp_prcp_perCollect[nxt_collect_indx]
                sprt_owed = self.sprt_prcp_perCollect[nxt_collect_indx]
            
            # add interest (we may have to adjust by +1 period)
            corp_owed += self.corp_intr_perPrd[prv_collect_prd:period].sum()\
                         + self.corp_pnlt_perPrd[prv_collect_prd:period].sum()
            sprt_owed += self.sprt_intr_perPrd[prv_collect_prd:period].sum()\
                         + self.sprt_pnlt_perPrd[prv_collect_prd:period].sum()
            
        return corp_owed, sprt_owed
          
    def to_dict(self):
        # outputs essential coupon attributes as a dict
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
