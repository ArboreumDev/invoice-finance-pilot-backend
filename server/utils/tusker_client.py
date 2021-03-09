# %%
import requests
from utils.invoice import raw_order_to_invoice

# TODO save thie in .env
TUSKER_TOKEN = "EKtk84IF9xzutyEMD-I_w35SlqcaXlOrKGcHIoxm3Ow"
TUSKER_STAGING_BASE_URL = "https://tusker-staging.logistimo.com/tusker-service"
TUSKER_USER_URL = "/search/users/suggestions"
TUSKER_ORDER_URL = "/orders/search"


class TuskerClient:
    """ code to connect Tusker API to our DB """
    def __init__(self, base_url=TUSKER_STAGING_BASE_URL):
        """ initialize client and """
        # TODO properly add logger
        # self.logger = get_logger(self.__class__.__name__)
        self.headers = {"Content-Type": "application/json", "LM_PA_TOKEN": TUSKER_TOKEN}
        self.base_url = base_url
        # TODO get this from other API
        self.customer_id = "58f1e776-c372-4ec5-8fa4-f30ab74ca631"

    def get_latest_invoices(self):
        # prob we need to add a parameter here to only fetch the latest invoices
        input = {
            "pl": {
                "c_id": self.customer_id,
                "o_sts": [3, 6, 13, 18, 21], # TODO replace those with enum
                "pg_no": 1,
                "size": 10,
                "s_by": "crt",
                "s_dir": 0,
            }
        }
        response = requests.post(self.base_url + TUSKER_ORDER_URL, json=input, headers=self.headers)
        if response.status_code == 200:
            raw_orders = response.json().get("pl", {}).get("orders", [])
            print(raw_orders)

            return raw_orders
            # return [raw_order_to_invoice(order) for order in raw_orders]

        else:
            # TODO implement custom exception class
            raise NotImplementedError(str(response.json()))

    def fetch_one_order(self, order_id):
        """ update a specific order """


# %%
tusker_client = TuskerClient(TUSKER_STAGING_BASE_URL)
# res = tc.get_latest_orders()
#
# print(orders.json())
# %%
