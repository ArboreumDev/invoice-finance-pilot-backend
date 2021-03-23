import numpy as np
import pandas as pd
import datetime as dt
from typing import List
from itertools import groupby
from collections import Counter
from scipy import optimize, special

from loan.coupon import Coupon
from common.loan import Repayment
from common.constant import (DEFAULT_DISCOUNT_APR,
                                     DEFAULT_PRECISION_MATH_OPERATIONS,
                                     DEFAULT_PRECISION_MONEY,
                                     DEFAULT_SUPPORTER_LAG)

class LoanMath:
    @staticmethod
    def convert_regular_payments_to_sequence(
        payments: List[Repayment], 
        start_date: dt.datetime, 
        days_per_period: int = 30):
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
    
    @staticmethod
    def convert_regular_payments_2_combined_dict(
        collections_corp: List,
        collections_sprt: List,
        start_date: dt.datetime,
        days_per_period: int = 30,
        keep_dates: bool = False,
        prv_repayments_dict: dict = {},
        collection_dates: List = []):
        """
        convert a list of payment-date-tuples to {period: (amount corpus, amount supporter)}
        with all payments from the same period added up into one
        """
        
        # helper function
        def convert_repayments_2_dict(repayments):
            # parse payment tuple
            parsed = [list(t) for t in zip(*repayments)]
            dates = parsed[0]
            payments = parsed[1]
            
            # convert dates to index
            if keep_dates:
                date_indx = dates
            else:
                date_indx = [int(np.floor((date-start_date).days/days_per_period)) for date in dates]
            
            #coalesce in case multiple payments in period
            pmnt_date_list = list(zip(date_indx,payments))
            coalesced = [[k, sum(v for _, v in g)] for k, g in groupby(sorted(pmnt_date_list), key = lambda x: x[0])]
            
            return {item[0]:item[1] for item in coalesced}
        
        # assert lenghts are the same
        assert len(collections_corp) == len(collections_sprt)
          
        # convert to dict with format {periods from start date: amount}
        if all(isinstance(item, tuple) for item in (collections_corp+collections_sprt)):
            collections_corp = convert_repayments_2_dict(collections_corp)
            collections_sprt = convert_repayments_2_dict(collections_sprt)
        elif all(isinstance(item, float) for item in (collections_corp+collections_sprt)):
            collections_corp = {collection_dates[i]:collections_corp[i] for i in range(0,len(collections_corp))}
            collections_sprt = {collection_dates[i]:collections_sprt[i] for i in range(0,len(collections_sprt))}

        # coalesce corpus and supporter dicts into one
        repayments_dict = {prd: tuple(( collections_corp[prd], collections_sprt[prd] )) \
                                    for prd in collections_corp }
        
        # combine with the previous repayments_dict if passed in
        if bool(prv_repayments_dict):
            combined_dict = {**prv_repayments_dict,**repayments_dict}

            # remove extraneous keys
            dates = sorted(combined_dict.keys())
            ## last non-None entry
            end_indx = np.where([combined_dict[date][0] is not None for date in reversed(dates)])[0][0]
            end_date = list(reversed(dates))[end_indx]
            ## remove
            selected = [date for date in dates if date<end_date and combined_dict[date][0] is None]
            for key in selected:
                combined_dict.pop(key, None)
            
            return combined_dict
        
        return repayments_dict

    @staticmethod
    def calc_IRR_NPV(
        loan_amt: float,
        loan_tnr: float,
        APR: float,
        discount_APR: float = DEFAULT_DISCOUNT_APR,
        prv_pmnts: List[float] = [],
        annual_cmpnd_prds: int = 12):
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
        if len(prv_pmnts)<loan_tnr:
            coupon = Coupon(prcp_corp = 0,
                            prcp_sprt = loan_amt,
                            APR_corp = APR,
                            APR_sprt = APR,
                            loan_tnr = loan_tnr,
                            prv_pmnts_corp = [0]*len(prv_pmnts),
                            prv_pmnts_sprt = prv_pmnts,
                            max_slope = 0,
                            annual_cmpnd_prds = annual_cmpnd_prds
                            ).to_dict()

            ideal_payments = coupon['sprt_collections']
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
        annual_cmpnd_prds: int = 12):
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
            IRR_hat, NPV = LoanMath.calc_IRR_NPV(
                loan_amt, loan_tnr, APR[0], discount_APR, prv_pmnts, annual_cmpnd_prds
            )
            return IRR_hat - IRR

        # Find Roots
        init_guess = discount_APR * 2 + IRR
        APR = optimize.fsolve(function_2_solve, init_guess)

        IRR_new, NPV = LoanMath.calc_IRR_NPV(
            loan_amt, loan_tnr, APR[0], discount_APR, prv_pmnts, annual_cmpnd_prds
        )

        return APR[0], NPV

    @staticmethod
    def calc_firstLoss_pct_val(
        pr_kum_loan: List[float], 
        init_collateral: float, 
        corp_prcp_outstand: float, 
        sprt_prcp_outstand: float):
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
        E_loss = lambda a, b, x: 1 - b * special.betainc((1 + 1 / a), b, x ** a)

        # collateral from first loss
        c_loss = E_loss(pr_kum_loan[0], pr_kum_loan[1], (1 - init_collateral) * (1 - v_sprt)) - E_loss(
            pr_kum_loan[0], pr_kum_loan[1], (1 - init_collateral)
        )

        return c_loss
    
    @staticmethod
    def calc_collection_dates(
        start_date: dt.datetime, 
        end_date: dt.datetime, 
        days_per_collection: int, 
        num_collections: int=0, 
        shift: bool=False):
        """
        calculates collection dates constrained such that
        (1) they all fall on same weekday
        (2) collections per month is consistent
        (3) collection dates are approximately same distance apart

        Parameters
        ----------
        start_date (dt.datetime): loan start_date
        end_date (dt.datetime): ignored if num_collections given, otherwise approx end_date
        days_per_collection (int): number of days between collections (min is 7)
        num_collections (int): number of collections which defines loan_tenor
        shift (bool): used by credit_line to speed up calculations

        Returns
        -------
        vector of dt.datetimes 
        """

        def num_days_between( start, end, week_day):
            num_weeks, remainder = divmod( (end-start).days, 7)
            if ( week_day - start.weekday() ) % 7 <= remainder:
                return num_weeks + 1
            else:
                return num_weeks
        
        # assertions
        if num_collections>0:
            end_date = start_date+dt.timedelta(days=days_per_collection*num_collections)
        
        # essential values
        month_offset = int(np.floor(days_per_collection/30))
        week_offset = int(np.floor((days_per_collection-30*month_offset)/7))
        day_offset = int(days_per_collection-30*month_offset-7*week_offset)
        start_weekday = start_date.strftime('%A')[0:3]
        start_week_of_month = num_days_between(start_date.replace(day=1),
                                            start_date,
                                            start_date.weekday())
        start_week_of_month = min(4,start_week_of_month)
        
        # fast forward start_date
        if shift:
            new_start_date = end_date+pd.DateOffset(months=-month_offset-1,
                                                    weeks=-week_offset-1,
                                                    days=-1)
            start_dates = pd.bdate_range(new_start_date,periods=1,
                                        freq='WOM-'+str(start_week_of_month)+start_weekday.upper())
            start_date = start_dates[0].to_pydatetime()
            
            
        # start_dates for additional series
        series_start_dates = [(start_date+pd.DateOffset(months=month_offset,days=-1)).to_pydatetime()]
        if week_offset>0:
            # permissable weeks series can begin on
            cycle = np.array([1,2,3,4]*3)
            week_starts = np.unique(cycle[np.arange(0,12,week_offset)[1:]-1])
            # week_starts = np.append(week_starts,[1] if week_offset==2 else [])
            # compute and store
            for i in week_starts:
                new_start_date = (start_date+pd.DateOffset(months=month_offset,
                                                        weeks=int(i),
                                                        days=-1)).to_pydatetime()
                series_start_dates = series_start_dates+[new_start_date]
                
        # initiate series
        series_dates = pd.bdate_range(start_date,end_date+dt.timedelta(days=days_per_collection),
                                        freq='WOM-'+str(start_week_of_month)+start_weekday.upper())

        # generate subsequent series
        period_len  = len(series_dates)+1
        for i in range(1,len(series_start_dates)):
            week_of_month = num_days_between(series_start_dates[i].replace(day=1),
                                            series_start_dates[i],
                                            start_date.weekday())+1
            week_of_month = 1 if week_of_month==5 else week_of_month
            dates = pd.bdate_range(series_start_dates[i],periods=max(2,period_len),
                                        freq='WOM-'+str(week_of_month)+start_weekday.upper())
            series_dates = series_dates.union(dates)
        
        # remove anything extraneous
        date_offset = pd.DateOffset(months=month_offset,weeks=week_offset)
        indx = np.where(series_dates >= (end_date+date_offset).to_pydatetime())[0]
        if indx.size>0:
            indx = min(indx)
        else:
            indx = len(series_dates)
        series_dates = series_dates[0:min(len(series_dates),(indx+1))]
        
        # filter dates to ensure they match interval
        ## to find closest date that matches, preferring the larger if tie
        def nearest(items, pivot):
            return min(items, key=lambda x: abs(x.timestamp() - pivot.timestamp())\
                                            -x.timestamp()/pivot.timestamp()*0.00001)

        ## to select items
        selected = []
        def select(series_dates,ideal):
            if len(selected) > 0:
                threshold = max(selected[-1] + date_offset,ideal)
            else:
                threshold = ideal
            v = nearest(series_dates,threshold)
            selected.append(v) 
            return v

        ideal_dates = pd.date_range(start_date,series_dates[-1]+date_offset,freq=date_offset)[1:]
        selected_dates = np.unique([select(series_dates,ideal) for ideal in ideal_dates])
        
        # filter again
        indx = min(np.where(selected_dates >= end_date)[0])
        selected_dates = selected_dates[0:min(len(selected_dates),(indx+1))]
        
        # compress if possible
        max_collections_per_month = max(Counter([i.month for i in selected_dates]).values())
        def remove_gap(series,indx):
            curr_date = series[indx]
            prv_date = series[indx-1]
            # check gap is between months
            if curr_date.month>prv_date.month:
                new_date = prv_date+date_offset
                # conditions that must be true to proceed
                if (new_date.month==curr_date.month and \
                    new_date.weekday()==curr_date.weekday() and \
                    new_date<curr_date):
                    # check we don't violate max_collections_per_month
                    diff = curr_date-new_date
                    rest_of_series = series[indx:]-diff
                    collections_per_month = max(Counter([i.month for i in rest_of_series]).values())
                    if collections_per_month<=max_collections_per_month:
                        new_series = np.append(series[0:indx],rest_of_series)
                        return new_series
            return series
        
        for indx in range(1,len(selected_dates)):
            selected_dates = remove_gap(selected_dates,indx)
            
        if num_collections>0:
            selected_dates=selected_dates[0:num_collections]

        return [x.to_pydatetime() for x in selected_dates]
