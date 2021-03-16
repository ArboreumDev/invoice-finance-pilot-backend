from fastapi import APIRouter, Depends, FastAPI, HTTPException
from pydantic import BaseModel
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED

from utils.common import Mapping, MappingInput
from utils.fullfill_loan import fulfill
from utils.rupeecircle_client import rc_client
from utils.security import check_jwt_token_role


class Item(BaseModel):
    id: str
    value: str


class Message(BaseModel):
    message: str


app = FastAPI()


# @app.get("/items/{item_id}", response_model=Item, responses={404: {"model": Message}})
# async def read_item(item_id: str):

# ======================== ENDPOINTS ==================================
mapping_app = APIRouter()

# #use this to exclude routes from docs
# @mapping_app.get("/test", include_in_schema=False)
# def t():
#     return {"OKTEST"}


# def _get_mapping(mapping_request: MappingInput, role: str = Depends(check_jwt_token)):
@mapping_app.post(
    "/mapping",
    response_model=Mapping,
    responses={HTTP_400_BAD_REQUEST: {"model": Message, "description": "Invalid Funds"}},
    tags=["RC"],
)
# def _get_mapping(mapping_request: MappingInput):
def _get_mapping(mapping_request: MappingInput, role: str = Depends(check_jwt_token_role)):
    if role != "rc":
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=f"Wrong permissions, role {role} not authorized")
    # TODO
    # get lender balances from RC-api
    lender_balances = rc_client.get_investor_balances(investor_ids=mapping_request.investor_ids)
    nonzero_balances = [1 for b in lender_balances.values() if b > 1000]
    if sum(nonzero_balances) < 4:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="there must be at least 4 lenders with balances>1000"
        )

    print(lender_balances)
    try:
        lender_contributions, _ = fulfill(mapping_request.loan_amount, lender_balances)
    except AssertionError as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))
        print(e)
    # call fill_loan
    return Mapping(allocations=lender_contributions)
