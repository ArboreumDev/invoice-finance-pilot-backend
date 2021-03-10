from typing import Any, List, Tuple, Dict

import copy
import numpy as np
import scipy as sp
from scipy import optimize
from iteround import saferound

def fulfill(
    loan_amount: float,
    lender_balances: Dict[Any,float],
    alpha: float = 2,
    weights: Any = None,
    penalty_coef: float = 1,
    #method: str = 'DiffEv',
    num_CPUs: int = 1      
    ):

    """
    Parameters
    ----------
    loan_amount (float): when was the first disbursement 
    lender_balances ({Lender_ID : Balance (float)}): dictionary of lender balances
    alpha (float): the higher alpha, the most sensitive to larger lender balances ()
    weights ({Lender_ID : Weight (float)}): weight attached to different lenders
    penalty_coef (float): if sum constraint is part of the objective function (>1)
                          or linear constraint on the topological manifold (0)
    (ignore) method (str): can be "DiffEv" for differential-evolution (only one that works in reasonable time),
                         "SHGO" for simplicial homology global optimization,
                         "BFGS" for localized gradient-descent (Broyden–Fletcher–Goldfarb–Shanno algorithm)
    num_CPUs (int): optimization can run faster using more CPUs (default 1)

    Returns:
    --------
    contributions ({Lender_ID : Contribution (float)}): dictionary of contribution per lender
    lender_balances ({Lender_ID : Balance (float)}): dictionary of new lender balances
    
    Note:
    -----
    For any future editor essential asserts to check constraints must be included
    """
    
    #parse dicts
    lender_IDs = list(lender_balances.keys())
    lender_balances = list(lender_balances.values())
    N = len(lender_balances)
    
    #convert to numpy
    contributions = np.full(N,0)
    lender_balances_original = copy.deepcopy(np.array(lender_balances))
    lender_balances = np.floor(np.array(lender_balances)/1000)*1000
    
    #assertions
    assert alpha>=0,'alpha must be non-negative'
    if weights is not None:
        assert len(weights)==N,"weights must be same length as lender_balances"
        weights = [weights[id] for id in lender_IDs]

    #precalculate some values for below function
    if alpha==0:
        beta = -1/N
    elif alpha==1:
        beta = 1/N
    else:
        beta= 1/(N*alpha*(alpha-1))
    
    #objective function to minimize (x=contribution)
    def generalized_entropy(x):
        
        y = lender_balances-x        
        mu = np.mean(y)        
        vals = (y/mu)**(alpha)-1
        
        if weights is None:
            entropy = beta*np.sum(vals)
        else:
            entropy = beta*np.sum(vals/weights)
         
        #penalty
        penalty = (np.sum(x)-(loan_amount-np.sum(contributions)))**2
        return entropy+penalty*penalty_coef
        
    #choose starting points
    def gen_start_point(loan_amount,lender_balances,ub):
        x0 = [max(lender_balances)*2]*N
        while np.any(x0>ub):
            x0 = np.random.multinomial(loan_amount/1000,
                                       ub/(1.5*loan_amount),
                                       1)[0]*1000
        return x0
    
    #set constraints
    total_is_loan_amt = lambda x: np.sum(x)-(loan_amount-np.sum(contributions))
    constraints = ({'type': 'eq', 'fun': total_is_loan_amt})
    lc = optimize.LinearConstraint(np.full([1,N],1),
                                   loan_amount,
                                   loan_amount)
    
    #optimizer
    def run_opt(lb,ub,penalty_coef,num_CPUs):
            
        if penalty_coef==0:
            rslt = optimize.differential_evolution(generalized_entropy,
                                                bounds=list(zip(lb,ub)),
                                                constraints = (lc),
                                                workers = num_CPUs)
        else:                                   
            rslt = optimize.differential_evolution(generalized_entropy,
                                                bounds=list(zip(lb,ub)),
                                                workers = num_CPUs)
        
        contributions = np.array(saferound(rslt.x/1000,0))*1000
        
        return contributions, rslt
            
    #set upper bound (25%)
    ub = np.full(N,np.floor(0.25*loan_amount/1000)*1000)
    ub = np.minimum(ub,lender_balances)
    #set lower bound (0)
    lb = np.full(N,0)
    
    #check if request is even possible
    if np.sum(ub)<loan_amount:
        print(f"Loan Amount {loan_amount}> funds available{np.sum(ub)}")
        raise AssertionError("insufficent funds")
         
        #create empty dicts
        lender_balances = dict(zip(lender_IDs,lender_balances_original))
        contributions = dict(zip(lender_IDs,[np.nan]*N))
        
        return contributions, lender_balances
    
    #run optimizer
    contributions, _ = run_opt(lb,ub,penalty_coef,num_CPUs)
    
    #rerun if rounding created issues
    ub2 = copy.copy(ub)
    while np.any(contributions>ub):
        ub2[contributions>ub] += -1000
        contributions, _ = run_opt(lb,ub2,penalty_coef,num_CPUs)
    
    #rerun if loan_amount does not add up
    if np.sum(contributions)!=loan_amount:
        contributions, _ = run_opt(lb,ub2,0,num_CPUs)
   
    #assertions
    assert np.sum(contributions)==loan_amount, \
          "Contributions equal "+str(np.sum(contributions))+", different from loan amount"
    for i in range(0,N):
        assert contributions[i]<=ub[i], \
               "invalid result, contribution of Lender "+str(lender_IDs[i])+" exceeds limit"

    #create dicts
    lender_balances = dict(zip(lender_IDs,lender_balances_original-contributions))
    contributions = dict(zip(lender_IDs,contributions))

    return contributions, lender_balances

# if method=="SHGO":
#     penalty_coef = max(1.0,penalty_coef)
#     rslt = optimize.shgo(generalized_entropy,
#                         bounds=list(zip(lb,ub)),
#                         n=500,iters=1)
# elif method=="DiffEv":
#     if num_CPUs <= 1:
#         num_CPUS = None
        
#     if penalty_coef==0:
#         rslt = optimize.differential_evolution(generalized_entropy,
#                                             bounds=list(zip(lb,ub)),
#                                             constraints = (lc),
#                                             workers = num_CPUs)
#     else:                                   
#         rslt = optimize.differential_evolution(generalized_entropy,
#                                             bounds=list(zip(lb,ub)),
#                                             workers = num_CPUs)
# else:
#     rslt = optimize.minimize(generalized_entropy,
#                             x0=gen_start_point(loan_amount-np.sum(contributions),
#                                                 lender_balances,
#                                                 ub),
#                             bounds=optimize.Bounds(lb,ub),
#                             constraints=[constraints])
