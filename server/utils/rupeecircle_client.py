# %%
# import os
# from random import randint
from typing import List

import requests

class FormData:
    def __init__(self):
        self.data = []

    def append(self, k, v):
        if isinstance(v, str) or isinstance(v, int) or isinstance(v, float):
            self.data.append((k, (None, v)))
        else:
            self.data.append((k, v))

config = {
    "RUPEE_CIRCLE_HOSTNAME": "http://sandbox.rupeecircle.com",
    # "RUPEE_CIRCLE_VERSION": "v3",
    "RUPEE_CIRCLE_EMAIL": "nupur.0905@gmail.com",
    "RUPEE_CIRCLE_PASSWORD": "Abcd@1234",
    # "RUPEE_CIRCLE_PARTNER_ID": "PIND1500",
    # "RUPEE_CIRCLE_DISBURSAL_EMAIL": "julius@arboreum.dev",
    "INVESTOR_API_USERNAME": "testpart@gmail.com",
    "INVESTOR_API_PASSWORD": "test123"
}

def result_to_balance(res):
    if type(res) == list:
        return res[0].get('available_balance', 0)
    else:
        return 0

class RupeeCircleClient:
    def __init__(self, base_url: str, email: str, password: str):
        """ initialize client and get access token from RC-sandbox """
        self.base_url = base_url
        self.password = password
        self.username = email
        self.headers = {}
        self.refresh_token()

    def refresh_token(self):
        form = FormData()
        form.append("email", self.username)
        form.append("password", self.password)
        auth_url = self.base_url + "/api/v1/clientSecretDetails"
        response = requests.request("POST", auth_url, data=form.data)
        data = response.json()
        if not data['flag']:
            raise AttributeError(data['message'])  # TODO define exception
        else:
            access_token = response.json()["data"]["token_details"]["access_token"]
            self.headers = {"Authorization": f"Bearer {access_token}"}

    def get_investor_balances(self, investor_ids: List[str]):
        self.refresh_token()
        url = self.base_url + "/api/v1/walletbalance"
        # response = requests.request("POST", url, json={"investor_id": investor_ids})
        response = requests.request("POST", url, json={"investor_id": investor_ids}, headers=self.headers)
        data = response.json()
        if not data['flag']:
            raise AttributeError(data['message'])  # TODO define exception
        else:
            balances = response.json()["data"]
            return {inv: result_to_balance(val) for inv,val in balances.items()}


rc_client = RupeeCircleClient(
    base_url=config["RUPEE_CIRCLE_HOSTNAME"],
    email=config["RUPEE_CIRCLE_EMAIL"],
    password=config["RUPEE_CIRCLE_PASSWORD"],
    # partner_id=config["RUPEE_CIRCLE_PARTNER_ID"],
    # disbursal_email=config["RUPEE_CIRCLE_DISBURSAL_EMAIL"]
)