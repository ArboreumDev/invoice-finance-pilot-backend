# %%
import copy
from typing import List

import requests

from utils.common import ReceiverInfo
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
            _input["pl"]["rcvr"]["id"] = receiver_id
        _input["pl"]["cust"]["id"] = customer_id if customer_id else self.customer_id

        response = requests.post(self.base_url + TUSKER_ORDER_URL, json=_input, headers=self.headers)
        if response.status_code == 200:
            new_order = response.json().get("pl", {})
            # print(new_order)
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
                {"op": "2", "path": "\\remarks", "val": "Arboreum Testing"},
            ]
        }
        url = f"{self.base_url}{TUSKER_ORDER_URL}/{invoice_id}"
        print(url)
        response = requests.patch(f"{self.base_url}{TUSKER_ORDER_URL}/{invoice_id}", json=_input, headers=self.headers)
        if response.status_code == 200:
            return True
        else:
            # TODO implement custom exception class
            raise NotImplementedError(str(response.json()))

    def customer_to_receiver_info(self, search_string: str, _city: str = "", _phone=""):
        _input = {"pl": {"type": 4, "p_txt": search_string, "stts": [0], "s_by": "name", "s_dir": 1}}
        response = requests.post(f"{self.base_url}/search/users/suggestions", json=_input, headers=self.headers)
        data = response.json()
        assert response.status_code == 200, "some error"
        users = data.get("pl").get("users")
        # assert users, "no user found"
        selected = ""
        found = []
        for user in users:
            city = user.get("loc").get("addr").get("city")
            phone = user.get("cntct").get("p_mob")
            rr = ReceiverInfo(id=user.get("id"), name=user.get("cntct").get("name"), phone=phone, city=city)
            found.append(rr)
            # print(rr)
            if _city in city:
                # print('found one',rr)
                if selected:
                    pass
                    # print('oho, double entry for', _city)
                else:
                    selected = rr

        return {"results":found, "match": selected}


# %%
tusker_client = TuskerClient(base_url=TUSKER_STAGING_BASE_URL, token=TUSKER_STAGING_TOKEN)
# res = tc.get_latest_orders()
#
# print(orders.json())
# %% code to create hitelist
searchtuples = [
    ("N K Pharma", "Bagalkot", "9480500862"),
    ("Sant Antonio Pharma", "Dandeli", "7760171632"),
    ("Rajendra Medical", "Haliyal", "9448778008"),
    ("New Shri manjunath medical & General Store", "Haliyal", "9632885458"),
    ("Mudabagil medicals", "Haliyal", "9845455958"),
    ("Geeta Medicals", "Haliyal", "9449988959"),
    ("Vansh Medical", "Haliyal", "9901331875"),
    ("Shrinivas Medical And General Store", "Haliyal", "9845456015"),
    ("Ganesh medical", "Haliyal", "9483135506"),
    ("Vidyashree medical", "Haliyal", "9900846420"),
    ("Sanjeevini medical", "Haveri", "9448139277"),
    ("New Haveri medical", "Haveri", "7975132991"),
    ("K G N Medical", "Kala", "9986840853"),
    ("Shri Shambhavi Med And Gen", "Kalas", "9686637521"),
    ("Shriram Medicals", "Kundagol", "9980381450"),
    ("Shri Kalmeshwar Medical", "Kundagol", "9113667708"),
    ("Shri Raghavendra Medical", "Kundagol", "9449121663"),
    ("Shivayogeshwar Medical", "Kundagol", "7406883791"),
    ("sainath medicals", "Kundagol", "9886913839"),
    ("Mahantesh Medical", "Kundagol", "9449642927"),
    ("Sainaath medical and general store", "Kundagol", "9945759225"),
    ("Padmamba Medical", "Laxmeshwa", "9148046108"),
    ("Agadi Sunrise Hospital Pvt Ltd", "Laxmeshwa", "8095294422"),
    ("Adinath Medical Stores", "Laxmeshwa", "8310653180"),
    ("Gangadhar Medical", "Laxmeshwa", "9448980902"),
    ("Shri Verabhadreshwar Medical Store", "Laxmeshwa", "9448186108"),
    ("Gourishankar Medical Store", "Saundatt", "8330222312"),
    ("Gurusparsha Medical And General Store", "Saundatt", "7353383821"),
    ("Shri Kalika Medical Stores", "Saundatti", "9880293524"),
    ("Mahesh Medical", "Saundatti", "9620073108"),
    ("Hanumant gad medical", "Saundatt", "8618903521"),
    ("Amareshwar Medicals", "Saundatt", "9113000177"),
    ("Shri Siddharoodha Medicals", "Shirur", "9535936595"),
    ("Shri Sai Medical Dhanguda Hospital", "Saundatti", "8971309257"),
    ("Nagareshwar Medical", "Saundatti", "9341397102"),
    ("Sangameshwar Med & Gen Stores", "Saundatti", "9448436752"),
]

whitelist = {}
missing = {}
duplicates = {}
match, toomany, none = 0, 0, 0
for t in searchtuples:
    name, city, phone = t[0], t[1], t[2]
    print("")
    print(f"looking for {name}, {phone}")
    r_info = tusker_client.customer_to_receiver_info(phone, city)
    if not r_info["match"]:
        if len(r_info["results"]) > 1:
            print(f"{name, city} --> DUPLICATE")
            toomany += 1
            duplicates[name] = r_info['results']
        else:
            print(f"{name, city} --> MISSING")
            missing[name] = r_info['results']
            none += 1
    elif r_info["match"]:
        print("-> match!")
        match += 1
        whitelist[r_info["match"].id] = r_info["match"]

print(f"found{match}, missing {none}, double{toomany}")

# %%
import pprint
# copy this into whitelist_mock_db.py:
pprint.pprint(whitelist)

# %%
