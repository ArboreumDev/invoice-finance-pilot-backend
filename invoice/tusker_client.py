# %%
import copy
from typing import List

import requests

from utils.constant import GURUGRUPA_CUSTOMER_ID, TUSKER_DEFAULT_NEW_ORDER

# TODO save thie in .env
TUSKER_STAGING_TOKEN = "EKtk84IF9xzutyEMD-I_w35SlqcaXlOrKGcHIoxm3Ow"
TUSKER_STAGING_BASE_URL = "https://tusker-staging.logistimo.com/tusker-service"
TUSKER_USER_URL = "/search/users/suggestions"
TUSKER_ORDER_URL = "/orders"
TUSKER_ORDER_SEARCH_URL = "/orders/search"

# TODO refactor status to be enum

code_to_status = {
    2: "PENDING",
    3: "PLACED_AND_VALID",
    4: "PENDING",
    6: "PICKED_BY_SHIPPER",
    9: "IN_TRANSIT",
    12: "IN_TRANSIT",
    13: "IN_TRANSIT",
    15: "IN_TRANSIT",
    18: "IN_TRANSIT",
    19: "IN_TRANSIT",
    21: "DELIVERED",
    24: "CANCELLED",
    27: "CANCELLED",
}

status_to_code = {
    "DELIVERED": [21],
    "CANCELLED": [24, 27],
    "IN_TRANSIT": [9, 12, 13, 15, 18, 19],
    "PICKED_BY_SHIPPER": [6],
    "PLACED_AND_VALID": [3],
    "PENDING": [2, 4],
}


def order_status_to_code(status: str):
    if status in status_to_code:
        return status_to_code[status][0]
    raise AssertionError(f"unknown order status: {status}")


def code_to_order_status(code: int):
    if code in code_to_status:
        return code_to_status[code]
    raise AssertionError(f"unknown status code: {code}")


# TODO refactor
STATUS_ELIGIBLE_FOR_FINANCING = [
    *status_to_code["PICKED_BY_SHIPPER"],
    *status_to_code["IN_TRANSIT"],
    *status_to_code["DELIVERED"],
    *status_to_code["PLACED_AND_VALID"],
]


class TuskerClient:
    """ code to connect Tusker API to our DB """

    def __init__(self, base_url: str, token: str, customer_id: str = GURUGRUPA_CUSTOMER_ID):
        """ initialize client and """
        # TODO properly add logger
        # self.logger = get_logger(self.__class__.__name__)
        self.headers = {"Content-Type": "application/json", "LM_PA_TOKEN": token}
        self.base_url = base_url
        # TODO get this from other API
        self.customer_id = customer_id

    def track_orders(self, reference_numbers: List[str], customer_id=""):
        raw_orders = []
        while reference_numbers:
            # TODO properly understand pagination
            to_be_fetched = reference_numbers[:10]
            del reference_numbers[:10]
            input = {"pl": {"o_ref_nos": to_be_fetched, "size": 10}}
            response = requests.post(self.base_url + TUSKER_ORDER_SEARCH_URL, json=input, headers=self.headers)
            if response.status_code == 200:
                orders = response.json().get("pl", {}).get("orders", [])
                raw_orders += orders
            else:
                # TODO implement custom exception class
                raise NotImplementedError(str(response.json()))
        return raw_orders

    def create_test_order(self, customer_id: str = "", receiver_id: str = ""):
        _input = copy.deepcopy(TUSKER_DEFAULT_NEW_ORDER)

        # plug in parameters if given
        if receiver_id:
            _input['pl']['rcvr']['id'] = receiver_id
        _input["pl"]["cust"]["id"] = customer_id if customer_id else self.customer_id

        response = requests.post(self.base_url + TUSKER_ORDER_URL, json=_input, headers=self.headers)
        if response.status_code == 200:
            new_order = response.json().get("pl", {})
            print(new_order)
            # return new_order
            return new_order["id"], new_order["ref_no"], new_order["status"]
        else:
            # TODO implement custom exception class
            raise NotImplementedError(str(response.json()))

    def mark_test_order_as(self, invoice_id, new_status: str = "DELIVERED"):
        """ change the status of a new order to """
        _input = {
            "pl": [
                {"op": "3", "path": "\\status", "val": str(order_status_to_code(new_status))},
                # NOTE: if we ever want to update other stuff it would go like this:
                # { "op": "2", "path": "\\remarks", "val": "Arboreum Testing" }
            ]
        }
        response = requests.patch(f"{self.base_url}{TUSKER_ORDER_URL}/{invoice_id}", json=_input, headers=self.headers)
        if response.status_code == 200:
            return True
        else:
            # TODO implement custom exception class
            raise NotImplementedError(str(response.json()))


# %%
tusker_client = TuskerClient(base_url=TUSKER_STAGING_BASE_URL, token=TUSKER_STAGING_TOKEN)
# res = tc.get_latest_orders()
#
# print(orders.json())
# %%
# def get_latest_orders(self, invoice_ids: List[str], customer_id: str = ""):
#     """ should get all invoices since the last time we fetched """
#     # prob we need to add a parameter here to only fetch the latest invoices
#     print("got", invoice_ids)
#     # TODO implement pagination here if len(invoice_ids > 10)
#     c_id = customer_id if customer_id else self.customer_id
#     raw_orders = []
#     while invoice_ids:
#         to_be_fetched = invoice_ids[:10]
#         del invoice_ids[:10]
#         input = {
#             "pl": {
#                 "c_id": c_id,
#                 "o_sts": STATUS_ELIGIBLE_FOR_FINANCING,
#                 "pg_no": 1,
#                 "size": 10,
#                 "s_by": "crt",
#                 "s_dir": 0,
#                 "ids": to_be_fetched,
#             }
#         }
#         response = requests.post(self.base_url + TUSKER_ORDER_URL, json=input, headers=self.headers)
#         if response.status_code == 200:
#             orders = response.json().get("pl", {}).get("orders", [])
#             raw_orders += orders
#         else:
#             # TODO implement custom exception class
#             raise NotImplementedError(str(response.json()))
#     return raw_orders
