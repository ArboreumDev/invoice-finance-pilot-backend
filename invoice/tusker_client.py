# %%
from typing import List

import requests

from utils.constant import GURUGRUPA_CUSTOMER_ID

# TODO save thie in .env
TUSKER_TOKEN = "EKtk84IF9xzutyEMD-I_w35SlqcaXlOrKGcHIoxm3Ow"
TUSKER_STAGING_BASE_URL = "https://tusker-staging.logistimo.com/tusker-service"
TUSKER_USER_URL = "/search/users/suggestions"
TUSKER_ORDER_URL = "/orders/search"


code_to_order_status = {
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

# TODO refactor
STATUS_ELIGIBLE_FOR_FINANCING = [
    *status_to_code["PICKED_BY_SHIPPER"],
    *status_to_code["IN_TRANSIT"],
    *status_to_code["DELIVERED"],
    *status_to_code["PLACED_AND_VALID"],
]


class TuskerClient:
    """ code to connect Tusker API to our DB """

    def __init__(self, base_url=TUSKER_STAGING_BASE_URL):
        """ initialize client and """
        # TODO properly add logger
        # self.logger = get_logger(self.__class__.__name__)
        self.headers = {"Content-Type": "application/json", "LM_PA_TOKEN": TUSKER_TOKEN}
        self.base_url = base_url
        # TODO get this from other API
        self.customer_id = GURUGRUPA_CUSTOMER_ID

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

    def track_orders(self, reference_numbers: List[str], customer_id=""):
        raw_orders = []
        while reference_numbers:
            # TODO properly understand pagination
            to_be_fetched = reference_numbers[:10]
            del reference_numbers[:10]
            input = {"pl": {"o_ref_nos": to_be_fetched, "size": 10}}
            response = requests.post(self.base_url + TUSKER_ORDER_URL, json=input, headers=self.headers)
            if response.status_code == 200:
                orders = response.json().get("pl", {}).get("orders", [])
                raw_orders += orders
            else:
                # TODO implement custom exception class
                raise NotImplementedError(str(response.json()))
        return raw_orders

    def fetch_one_order(self, order_id):
        """ update a specific order """


# %%
tusker_client = TuskerClient(TUSKER_STAGING_BASE_URL)
# res = tc.get_latest_orders()
#
# print(orders.json())
# %%
