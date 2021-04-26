from utils.common import ReceiverInfo, WhiteListEntry
import os
from dotenv import load_dotenv


load_dotenv()

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

GURUGRUPA_RECEIVERS = {
    '030a0c98-d7e2-473c-afba-bed41feb2960': ReceiverInfo(id='dd06ff1a-d9f2-4b2a-8182-d9d2e9522d8e', name='SHri verabhadreshwar medical store', phone='+91-9448186108', city='Laxmeshwar', location_id='030a0c98-d7e2-473c-afba-bed41feb2960'),
    '0defef39-5123-45c2-90cf-0ddc5845cdaf': ReceiverInfo(id='b7116c9a-583c-4d94-b4d3-57f177d3b2a9', name='Shri sai Medical Dhanguda Hospital', phone='+91-8971309257', city='Saundatti', location_id='0defef39-5123-45c2-90cf-0ddc5845cdaf'),
    '0f9804fd-75d3-46b1-8cbf-c7da8bd675f3': ReceiverInfo(id='07e97ba4-c523-4a44-af0c-b8cba42a2b9f', name='Padmamba medical', phone='+91-9148046108', city='Laxmeshwar', location_id='0f9804fd-75d3-46b1-8cbf-c7da8bd675f3'),
    '1799d358-16f2-439d-b78c-c3a155aecfbf': ReceiverInfo(id='5a32414d-fca3-445e-8f12-ee6e59aa6872', name='sainath medicals', phone='+91-9886913839', city='Kundagol', location_id='1799d358-16f2-439d-b78c-c3a155aecfbf'),
    '234dcea7-3549-429e-aa7c-ebad46065040': ReceiverInfo(id='e49d4a96-c7f9-4c3a-929d-4b0a8b0afbee', name='Shrinivas medical and general store', phone='+91-9845456015', city='Haliyal', location_id='234dcea7-3549-429e-aa7c-ebad46065040'),
    '2a28cedb-2e2e-455f-af20-074a98a71cbe': ReceiverInfo(id='dc554af6-1e4f-401b-801d-4c053e48a038', name='Gourishankar medical store', phone='+91-8330222312', city='Saundatti', location_id='2a28cedb-2e2e-455f-af20-074a98a71cbe'),
    '318238e0-759e-4db7-8db7-8c71cb1078b1': ReceiverInfo(id='3a18ce32-0fa3-4a3d-a0cb-7300ef7135c6', name='Nagareshwar medical', phone='+91-9845448371', city='Saundatti', location_id='318238e0-759e-4db7-8db7-8c71cb1078b1'),
    '43e71a83-2f2f-4930-8266-012b68f5e174': ReceiverInfo(id='8ddf98e5-1a6f-406d-8192-8e68118e120f', name='Geeta Medicals', phone='+91-9449988959', city='Haliyal', location_id='43e71a83-2f2f-4930-8266-012b68f5e174'),
    '47eee331-0405-425c-b14c-3dac9b2684e0': ReceiverInfo(id='fa6f8e57-53d0-4997-8ac8-b45718cf1131', name='Rajendra Medical', phone='+91-9448778099', city='Haliyal', location_id='47eee331-0405-425c-b14c-3dac9b2684e0'),
    '4c6f96c0-bcb3-48d4-bf29-d7b48dbbba47': ReceiverInfo(id='7b132094-c537-44fd-8ec1-924e8f190fa2', name='Mudabagil medicals', phone='+91-9845455958', city='Haliyal', location_id='4c6f96c0-bcb3-48d4-bf29-d7b48dbbba47'),
    '50316dbc-0e41-43c6-96a1-36da983e701c': ReceiverInfo(id='ad38d0dd-76db-41b3-9eb9-dcdfbcff1e07', name='Shriram Medicals', phone='+91-9980381541', city='Kundagol', location_id='50316dbc-0e41-43c6-96a1-36da983e701c'),
    '5b09679a-de94-4154-b279-315d746b822a': ReceiverInfo(id='06708c2d-da8c-44f7-a237-fc7be592aa87', name='Shri Raghavendra Medical', phone='+91-9449121663', city='Kundagol', location_id='5b09679a-de94-4154-b279-315d746b822a'),
    '5d108d97-b190-4ee3-ba76-c6a501732b1d': ReceiverInfo(id='0edf7c64-dd61-4955-9222-ca34e5b1250a', name='Shri Kalika Medical Stores', phone='+91-9880293524', city='Saundatti', location_id='5d108d97-b190-4ee3-ba76-c6a501732b1d'),
    '6a40ee7e-11fa-49d5-ad82-a693aecab567': ReceiverInfo(id='096a33e5-e461-47e0-a05d-117199734b78', name='Hanumant gad medical', phone='+91-8618903521', city='Saundatti', location_id='6a40ee7e-11fa-49d5-ad82-a693aecab567'),
    '817e9c79-aa26-4789-8992-1f96ab417d24': ReceiverInfo(id='e85ab662-1da5-4628-acb9-e240fa6b399f', name='Sainaath medical and general store', phone='+91-9945759225', city='Kundagol', location_id='817e9c79-aa26-4789-8992-1f96ab417d24'),
    '81949b9f-6863-4e49-b66e-8ca24a49d57b': ReceiverInfo(id='60744e42-bf52-4238-93ca-d173ef9e132a', name='Agadi Sunrise Hospital pvt ltd', phone='+91-848727536', city='Laxmeshwar', location_id='81949b9f-6863-4e49-b66e-8ca24a49d57b'),
    '8ab660b6-a735-4f9f-aae5-2a5469ba51a1': ReceiverInfo(id='80e19233-0dd4-459c-8d43-57d0efc88358', name='Shri siddharoodha medicals', phone='+91-9535936595', city='Shirur', location_id='8ab660b6-a735-4f9f-aae5-2a5469ba51a1'),
    '8c8ec88f-0cb8-4490-af3a-0cb6494b10aa': ReceiverInfo(id='69ec5814-0f7d-4f26-8272-f3c1cbc086b2', name='SANGAMESHWAR MED & GEN STORES', phone='+91-9448436752', city='Saundatti', location_id='8c8ec88f-0cb8-4490-af3a-0cb6494b10aa'),
    '96ae2879-6e7a-4a3c-8a94-262efb30edfa': ReceiverInfo(id='a09151ca-77ab-44ad-9740-8e8b3db6623e', name='New Haveri medical', phone='+91-7975132991', city='Haveri', location_id='96ae2879-6e7a-4a3c-8a94-262efb30edfa'),
    'b4abf0c9-4c49-4e75-bf02-95ce93a66cfa': ReceiverInfo(id='13f4d15c-b702-4a18-abc9-6d5d157979a8', name='Vidyashree medical', phone='+91-9900846420', city='Haliyal', location_id='b4abf0c9-4c49-4e75-bf02-95ce93a66cfa'),
    'c2e25010-deca-4fc5-8709-82ae54f61d44': ReceiverInfo(id='87385325-0929-4990-99f5-002bfdef6dbd', name='Gangadhar Medical', phone='+91-9448980902', city='Laxmeshwar', location_id='c2e25010-deca-4fc5-8709-82ae54f61d44'),
    'c40e52b4-508b-44f3-a3ed-b1c5b1594fb2': ReceiverInfo(id='f1ac0c02-8b5a-4686-ba30-ab1829195496', name='Adinath Medical Store', phone='+91-9964732282', city='Laxmeshwar', location_id='c40e52b4-508b-44f3-a3ed-b1c5b1594fb2'),
    'c4c6e3b1-9ad0-4983-b90c-840df90a075b': ReceiverInfo(id='59664c85-70c4-4dce-b0ea-4d65d6051e2e', name='Shri ganesh medical', phone='+91-8762165566', city='Haliyal', location_id='c4c6e3b1-9ad0-4983-b90c-840df90a075b'),
    'ce2ac1af-2cb3-4ff3-8720-0e804be7f1c6': ReceiverInfo(id='03ca4dfd-dab1-44bf-8fed-548a065405a3', name='gurusparsha medical and general store', phone='+91-7353383821', city='Saundatti', location_id='ce2ac1af-2cb3-4ff3-8720-0e804be7f1c6'),
    'd91e0018-323e-429b-91e8-e737f544f756': ReceiverInfo(id='0adfea13-7672-4218-8292-6e2b092187d9', name='Mahesh Medicale', phone='+91-9341937037', city='Saundatti', location_id='d91e0018-323e-429b-91e8-e737f544f756'),
    'd94b7739-28b6-41b4-970a-422aa6dd726e': ReceiverInfo(id='171bf0af-3152-4ea6-b9fc-7dd8e36f1e1d', name='K G N Medical', phone='+91-9986840853', city='Kalas', location_id='d94b7739-28b6-41b4-970a-422aa6dd726e'),
    'e0f2c12d-9371-4863-a39a-0037cd6c711b': ReceiverInfo(id='aa8b8369-be51-49a3-8419-3d1eb8c4146c', name='Mahantesh Medical', phone='+91-9449642927', city='Kundagol', location_id='e0f2c12d-9371-4863-a39a-0037cd6c711b'),
    'e611c64d-4dc4-4fce-b99c-93ea88b8951e': ReceiverInfo(id='bda26d12-aee7-45e0-9686-1b173b839004', name='New Shri manjunath medical & General Store', phone='+91-9632885549', city='Haliyal', location_id='e611c64d-4dc4-4fce-b99c-93ea88b8951e'),
    'ec5daa93-a2e4-4193-a65f-25b15d97c7ca': ReceiverInfo(id='fcba19ca-b98b-4183-b58e-0e00484246eb', name='Shri Kalmeshwar Medical', phone='+91-9448322713', city='Kundagol', location_id='ec5daa93-a2e4-4193-a65f-25b15d97c7ca'),
    'ed7bf996-b805-4415-a990-195b50140921': ReceiverInfo(id='9e682e92-2350-4e8c-bba5-457e8ab94ded', name='shri shambhavi med and gen', phone='+91-9686637521', city='Kalas', location_id='ed7bf996-b805-4415-a990-195b50140921'),
    'f4264545-6f96-4c12-b388-aa543187c5d8': ReceiverInfo(id='2a6d415a-cc16-439f-83a6-95d1336db5bb', name='vansh medical', phone='+91-9901331875', city='Haliyal', location_id='f4264545-6f96-4c12-b388-aa543187c5d8'),
    'f5824c53-c43b-4035-85df-9d8bdc7bd077': ReceiverInfo(id='d9abccd6-e4c7-445c-bc18-5db251c2865b', name='Sanjeevini medicals', phone='+91-9448139277', city='Haveri', location_id='f5824c53-c43b-4035-85df-9d8bdc7bd077')
}


GURUGRUPA_CUSTOMER_ID = os.getenv("GURUGRUPA_CUSTOMER_ID")

PROD_WHITELIST_DB = {
    GURUGRUPA_CUSTOMER_ID: {r: WhiteListEntry(receiver_info=GURUGRUPA_RECEIVERS[r], credit_line_size=50000) for r in GURUGRUPA_RECEIVERS}
}
