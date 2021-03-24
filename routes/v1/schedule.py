from fastapi import APIRouter, Depends, FastAPI, HTTPException
from pydantic import BaseModel
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_500_INTERNAL_SERVER_ERROR
from utils.common import Mapping, MappingInput, BasicCouponInput, BasicCouponOutput
from utils.fullfill_loan import fulfill
from utils.rupeecircle_client import rc_client
from utils.security import check_jwt_token_role
from loan.couponTypes import generate_coupon
import numpy as np


class Item(BaseModel):
    id: str
    value: str


class Message(BaseModel):
    message: str


app = FastAPI()


# ======================== ENDPOINTS ==================================
schedule_app = APIRouter()

# #use this to exclude routes from docs
# @mapping_app.get("/test", include_in_schema=False)
# def t():
#     return {"OKTEST"}


# def _get_mapping(mapping_request: MappingInput, role: str = Depends(check_jwt_token)):
@schedule_app.post(
    "/coupon",
    response_model=BasicCouponOutput,
    responses={HTTP_500_INTERNAL_SERVER_ERROR: {"model": Message, "description": "Internal Error. Please contact arboreum!"}},
    tags=["RC"],
)
def _get_schedule(coupon: BasicCouponInput, role: str = Depends(check_jwt_token_role)):
    print('got ', coupon)
    if "rc" not in role:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=f"Wrong permissions, role {role} not authorized")
    try:
        coupon = generate_coupon(
            prcp_corp=0,
            prcp_sprt=coupon.principal,
            APR_corp=coupon.apr,
            APR_sprt=coupon.apr,
            loan_tnr=coupon.loan_tenor,
            prv_pmnts_corp=[0]*len(coupon.previous_payments),
            prv_pmnts_sprt=coupon.previous_payments,
            balloon_params=coupon.balloon_params,
            subsprt_info={},
            APR_pnlt=coupon.apr_penalty,
            annual_cmpnd_prds=coupon.annual_compound_periods,
            collection_dates=coupon.collection_dates,
            collection_freq=coupon.collection_frequency,
            max_slope=0,
        )
        _keys = [
            'sprt_collections', 'sprt_collect_full_repay', 'sprt_collect_current', 'sprt_prcp_perCollect',
            'sprt_intr_perCollect', 'sprt_pnlt_perCollect', 'sprt_intr_owed', 'sprt_intr_paid',
            'sprt_prcp_owed', 'sprt_prcp_paid',
        ]
        def to_list(value):
            if isinstance(value, np.ndarray):
                return list(value)
            return value
        #     arrays = [
        #         'sprt_collections', 'sprt_collect_full_repay', 'sprt_collect_current', 'sprt_prcp_perCollect',
        #         'sprt_intr_perCollect' 
        #     ]
        #     if key in []

        ret = {k: to_list(v) for k,v in coupon.to_dict().items() if k in _keys}
        print(ret)
        return BasicCouponOutput(
            coupon=ret
        )

    except Exception as e:
        print(e)
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

