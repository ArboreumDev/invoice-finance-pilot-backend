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
    '03ca4dfd-dab1-44bf-8fed-548a065405a3': ReceiverInfo(id='03ca4dfd-dab1-44bf-8fed-548a065405a3', name='gurusparsha medical and general store', phone='+91-7353383821', city='Saundatti'),
    '06708c2d-da8c-44f7-a237-fc7be592aa87': ReceiverInfo(id='06708c2d-da8c-44f7-a237-fc7be592aa87', name='Shri Raghavendra Medical', phone='+91-9449121663', city='Kundagol'),
    '069613d4-5cba-42cb-8709-2cf0ef3bf13e': ReceiverInfo(id='069613d4-5cba-42cb-8709-2cf0ef3bf13e', name='amareshwar medi', phone='+91-9113000177', city='Saundatti'),
    '07e97ba4-c523-4a44-af0c-b8cba42a2b9f': ReceiverInfo(id='07e97ba4-c523-4a44-af0c-b8cba42a2b9f', name='Padmamba medical', phone='+91-9148046108', city='Laxmeshwar'),
    '096a33e5-e461-47e0-a05d-117199734b78': ReceiverInfo(id='096a33e5-e461-47e0-a05d-117199734b78', name='Hanumant gad medical', phone='+91-8618903521', city='Saundatti'),
    '0edf7c64-dd61-4955-9222-ca34e5b1250a': ReceiverInfo(id='0edf7c64-dd61-4955-9222-ca34e5b1250a', name='Shri Kalika Medical Stores', phone='+91-9880293524', city='Saundatti'),
    '13f4d15c-b702-4a18-abc9-6d5d157979a8': ReceiverInfo(id='13f4d15c-b702-4a18-abc9-6d5d157979a8', name='Vidyashree medical', phone='+91-9900846420', city='Haliyal'),
    '171bf0af-3152-4ea6-b9fc-7dd8e36f1e1d': ReceiverInfo(id='171bf0af-3152-4ea6-b9fc-7dd8e36f1e1d', name='K G N Medical', phone='+91-9986840853', city='Kalas'),
    '1da66dbf-ebcb-4ab9-b48a-3410c4e7ed3e': ReceiverInfo(id='1da66dbf-ebcb-4ab9-b48a-3410c4e7ed3e', name='Mahesh Medical', phone='+91-9620073108', city='Saundatti'),
    '1f07b8ac-c0ad-454c-8ffa-4ef442eb4cfc': ReceiverInfo(id='1f07b8ac-c0ad-454c-8ffa-4ef442eb4cfc', name='J k medical', phone='+91-9480500862', city='Bagalkot'),
    '2a6d415a-cc16-439f-83a6-95d1336db5bb': ReceiverInfo(id='2a6d415a-cc16-439f-83a6-95d1336db5bb', name='vansh medical', phone='+91-9901331875', city='Haliyal'),
    '4cadd7e6-510e-4204-ba59-c04812e2f687': ReceiverInfo(id='4cadd7e6-510e-4204-ba59-c04812e2f687', name='Sangameshwar medical', phone='+91-8073722107', city='Saundatti'),
    '5a32414d-fca3-445e-8f12-ee6e59aa6872': ReceiverInfo(id='5a32414d-fca3-445e-8f12-ee6e59aa6872', name='sainath medicals', phone='+91-9886913839', city='Kundagol'),
    '60744e42-bf52-4238-93ca-d173ef9e132a': ReceiverInfo(id='60744e42-bf52-4238-93ca-d173ef9e132a', name='Agadi Sunrise Hospital pvt ltd', phone='+91-848727536', city='Laxmeshwar'),
    '60db9f51-18a7-4426-bd54-0b0d27b69103': ReceiverInfo(id='60db9f51-18a7-4426-bd54-0b0d27b69103', name='Ganesh Medical', phone='+91-9483135506', city='Haliyal'),
    '7b132094-c537-44fd-8ec1-924e8f190fa2': ReceiverInfo(id='7b132094-c537-44fd-8ec1-924e8f190fa2', name='Mudabagil medicals', phone='+91-9845455958', city='Haliyal'),
    '80e19233-0dd4-459c-8d43-57d0efc88358': ReceiverInfo(id='80e19233-0dd4-459c-8d43-57d0efc88358', name='Shri siddharoodha medicals', phone='+91-9535936595', city='Shirur'),
    '87385325-0929-4990-99f5-002bfdef6dbd': ReceiverInfo(id='87385325-0929-4990-99f5-002bfdef6dbd', name='Gangadhar Medical', phone='+91-9448980902', city='Laxmeshwar'),
    '8ddf98e5-1a6f-406d-8192-8e68118e120f': ReceiverInfo(id='8ddf98e5-1a6f-406d-8192-8e68118e120f', name='Geeta Medicals', phone='+91-9449988959', city='Haliyal'),
    '9e682e92-2350-4e8c-bba5-457e8ab94ded': ReceiverInfo(id='9e682e92-2350-4e8c-bba5-457e8ab94ded', name='shri shambhavi med and gen', phone='+91-9686637521', city='Kalas'),
    'a0392282-43fc-4d77-bbaa-475b3c677753': ReceiverInfo(id='a0392282-43fc-4d77-bbaa-475b3c677753', name='nagareshwar medical', phone='+91-9341397102', city='Saundatti'),
    'a09151ca-77ab-44ad-9740-8e8b3db6623e': ReceiverInfo(id='a09151ca-77ab-44ad-9740-8e8b3db6623e', name='New Haveri medical', phone='+91-7975132991', city='Haveri'),
    'aa8b8369-be51-49a3-8419-3d1eb8c4146c': ReceiverInfo(id='aa8b8369-be51-49a3-8419-3d1eb8c4146c', name='Mahantesh Medical', phone='+91-9449642927', city='Kundagol'),
    'ad38d0dd-76db-41b3-9eb9-dcdfbcff1e07': ReceiverInfo(id='ad38d0dd-76db-41b3-9eb9-dcdfbcff1e07', name='Shriram Medicals', phone='+91-9980381541', city='Kundagol'),
    'b7116c9a-583c-4d94-b4d3-57f177d3b2a9': ReceiverInfo(id='b7116c9a-583c-4d94-b4d3-57f177d3b2a9', name='Shri sai Medical Dhanguda Hospital', phone='+91-8971309257', city='Saundatti'),
    'bda26d12-aee7-45e0-9686-1b173b839004': ReceiverInfo(id='bda26d12-aee7-45e0-9686-1b173b839004', name='New Shri manjunath medical & General Store', phone='+91-9632885549', city='Haliyal'),
    'd9abccd6-e4c7-445c-bc18-5db251c2865b': ReceiverInfo(id='d9abccd6-e4c7-445c-bc18-5db251c2865b', name='Sanjeevini medicals', phone='+91-9448139277', city='Haveri'),
    'dc554af6-1e4f-401b-801d-4c053e48a038': ReceiverInfo(id='dc554af6-1e4f-401b-801d-4c053e48a038', name='Gourishankar medical store', phone='+91-8330222312', city='Saundatti'),
    'dd06ff1a-d9f2-4b2a-8182-d9d2e9522d8e': ReceiverInfo(id='dd06ff1a-d9f2-4b2a-8182-d9d2e9522d8e', name='SHri verabhadreshwar medical store', phone='+91-9448186108', city='Laxmeshwar'),
    'e49d4a96-c7f9-4c3a-929d-4b0a8b0afbee': ReceiverInfo(id='e49d4a96-c7f9-4c3a-929d-4b0a8b0afbee', name='Shrinivas medical and general store', phone='+91-9845456015', city='Haliyal'),
    'e85ab662-1da5-4628-acb9-e240fa6b399f': ReceiverInfo(id='e85ab662-1da5-4628-acb9-e240fa6b399f', name='Sainaath medical and general store', phone='+91-9945759225', city='Kundagol'),
    'f262050f-1a61-4614-818a-72931612583e': ReceiverInfo(id='f262050f-1a61-4614-818a-72931612583e', name='Adinath Medical', phone='+91-8310653180', city='Laxmeshwar'),
    'fa6f8e57-53d0-4997-8ac8-b45718cf1131': ReceiverInfo(id='fa6f8e57-53d0-4997-8ac8-b45718cf1131', name='Rajendra Medical', phone='+91-9448778099', city='Haliyal'),
    'fcba19ca-b98b-4183-b58e-0e00484246eb': ReceiverInfo(id='fcba19ca-b98b-4183-b58e-0e00484246eb', name='Shri Kalmeshwar Medical', phone='+91-9448322713', city='Kundagol')
}



GURUGRUPA_CUSTOMER_ID = os.getenv("GURUGRUPA_CUSTOMER_ID")

PROD_WHITELIST_DB = {
    GURUGRUPA_CUSTOMER_ID: {r: WhiteListEntry(receiver_info=GURUGRUPA_RECEIVERS[r], credit_line_size=50000) for r in GURUGRUPA_RECEIVERS}
}
