# %%
import requests

# TODO save thie in .env
TUSKER_TOKEN = "EKtk84IF9xzutyEMD-I_w35SlqcaXlOrKGcHIoxm3Ow"
TUSKER_STAGING_BASE_URL = "https://tusker-staging.logistimo.com/tusker-service"
TUSKER_USER_URL = "/search/users/suggestions"
TUSKER_ORDER_URL = "/orders/search"

class TuskerClient:
    def __init__(self, base_url):
        """ initialize client and """
        # TODO properly add logger
        # self.logger = get_logger(self.__class__.__name__)
        self.headers = {
            "Content-Type": "application/json",
            "LM_PA_TOKEN": TUSKER_TOKEN
        }
        self.base_url = base_url
        # TODO get this from other API
        self.customer_id = "58f1e776-c372-4ec5-8fa4-f30ab74ca631"

    
    def get_latest_orders(self):
        input = {
            "pl": {
                "c_f_dt": 1575868644499,
                "c_t_dt": 1687493544499,
                "c_id": self.customer_id,
                "o_sts": [
                    3, 6, 13, 18,21
                ],
                "pg_no": 1,
                "size": 2,
                "s_by": "crt",
                "s_dir": 0
            }
        }
        response = requests.post(self.base_url + TUSKER_ORDER_URL, json=input, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else: 
            # TODO implement custom exception class
            raise NotImplementedError(str(response.json()))

# %%
# tc = TuskerClient(TUSKER_STAGING_BASE_URL)
# res = tc.get_latest_orders()
# 
# print(orders.json())
# %%
