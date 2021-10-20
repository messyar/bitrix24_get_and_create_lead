import unittest
import requests
import json
from os import environ

from app import (
    create_or_update_b24_deal,
    deal_exist,
    check_fields_in_request,
    serialize_deal
)
from bitrix24 import Bitrix24

try:
    api_key = environ['API_KEY']
    url_to_request = 'http://127.0.0.1:5000' + '/deal/' + api_key + '/'
except Exception as name_error:
    print("Can't find Environment variable %s" % name_error)

try:
    url_to_b24 = environ['URL_TO_B24']
    # creating instance of Bitrix24 class
    bx24 = Bitrix24(url_to_b24)
except Exception as name_error:
    print("Can't find Environment variable %s" % name_error)

headers = {'Content-Type': 'application/json'}


class TestData:
    right_test_data = {
        "title": "test_title",
        "description": "Some description",
        "products": ["Candy", "Carrot", "Potato"],
        "delivery_adress": "st. Mira, 211, Ekaterinburg",
        "delivery_code": "#0123abCdeFg",
        "delivery_date": "2021-01-01:01:00",
        "client": {
            "name": "Test",
            "surname": "Testov",
            "phone": "+79098765432",
            "adress": "st. Mira, 287, Moscow"
        }
    }

    right_serialized_test_data = {
        "TITLE": "test_title",
        "UF_CRM_DESCRIPTION": "Some description",
        "UF_CRM_PRODUCTS": "Candy, Carrot, Potato",
        "UF_CRM_DELIVERY_ADRESS": "st. Mira, 211, Ekaterinburg",
        "UF_CRM_DELIVERY_CODE": "%230123abCdeFg",
        "UF_CRM_DELIVERY_DATE": "2021-01-01:01:00"
    }

    wrong_test_data1 = {
        "title": "bad_title",
        "cookies": "tasty"

    }

    wrong_test_data1_serialized = {
        "TITLE": "bad_title",
        "COOKIES": "tasty"
    }

    wrong_test_data2 = {
        "title": "bad_title",
        "client": {
            "name": "Test",
            "surname": "Testov",
            "phone": "+79098765432",
            "adress": "st. Mira, 287, Moscow"
        }

    }

    wrong_test_data2_serialized = {
        "TITLE": "bad_title",
    }

    def del_test_deal(self):
        found_deal = deal_exist(self.right_test_data['delivery_code'])
        if found_deal:
            bx24.callMethod("crm.deal.delete", id=found_deal['ID'])


test_data = TestData()


class TestAppREST(unittest.TestCase):

    def test_post_deal_200(self):
        json_data = json.dumps(TestData.right_test_data)
        response = requests.post(url_to_request, data=json_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        test_data.del_test_deal()

    def test_post_deal_400(self):
        json_data = json.dumps(TestData.wrong_test_data1)
        response = requests.post(url_to_request, data=json_data, headers=headers)
        self.assertEqual(response.status_code, 400)


class TestAppFunctions(unittest.TestCase):

    def test_create_or_update_b24_deal_200(self):

        response = create_or_update_b24_deal(test_data.right_test_data)
        self.assertEqual(response['code'], 200)
        self.assertEqual(response['data'], test_data.right_test_data)
        test_data.del_test_deal()

    def test_create_or_update_b24_deal_400(self):
        response = create_or_update_b24_deal(test_data.wrong_test_data1)
        self.assertEqual(response['code'], 400)

    def test_create_or_update_b24_deal_400_2_case (self):
        response = create_or_update_b24_deal(test_data.wrong_test_data2)
        self.assertEqual(response['code'], 400)

    def test_check_check_fields_in_request_right(self):
        response = check_fields_in_request(test_data.right_test_data)
        self.assertEqual(response['code'], 200)

    def test_check_check_fields_in_request_wrong1(self):
        response = check_fields_in_request(test_data.wrong_test_data1)
        self.assertEqual(response['code'], 400)

    def test_check_check_fields_in_request_wrong2(self):
        response = check_fields_in_request(test_data.wrong_test_data2)
        self.assertEqual(response['code'], 400)

    def test_serialize_deal_1(self):
        serialized_deal = serialize_deal(test_data.right_test_data)
        self.assertEqual(serialized_deal, test_data.right_serialized_test_data)

    def test_serialize_deal_2(self):
        serialized_deal = serialize_deal(test_data.wrong_test_data1)
        self.assertEqual(serialized_deal, test_data.wrong_test_data1_serialized)

    def test_serialize_deal_3(self):
        serialized_deal = serialize_deal(test_data.wrong_test_data2)
        self.assertEqual(serialized_deal, test_data.wrong_test_data2_serialized)

    def test_serialize_deal_negative(self):
        serialized_data = serialize_deal('Test data')
        self.assertFalse(serialized_data)
