from bitrix24 import Bitrix24, BitrixError
import requests
from flask import Flask, jsonify, request
from os import environ
from pprint import pprint
import re

web_app = Flask(__name__)
api_key = environ['API_KEY']
url_to_request = '/deal/' + api_key + '/'
url_to_b24 = environ['URL_TO_B24']

# creating instance of Bitrix24 class
bx24 = Bitrix24(url_to_b24)


class Fields:
    fields_bx24 = [
        {"FIELD_NAME": "DESCRIPTION",
         "ALT_FIELD_NAME_BX24": "UF_CRM_DESCRIPTION",
         "EDIT_FORM_LABEL": "Описание",
         "LIST_COLUMN_LABEL": "Описание",
         "USER_TYPE_ID": "string",
         "XML_ID": "DESCRIPTION"
         },
        {"FIELD_NAME": "PRODUCTS",
         "ALT_FIELD_NAME_BX24": "UF_CRM_PRODUCTS",
         "EDIT_FORM_LABEL": "Товары",
         "LIST_COLUMN_LABEL": "Товары",
         "USER_TYPE_ID": "string",
         "XML_ID": "PRODUCTS"
         },
        {"FIELD_NAME": "DELIVERY_ADRESS",
         "ALT_FIELD_NAME_BX24": "UF_CRM_DELIVERY_ADRESS",
         "EDIT_FORM_LABEL": "Адрес доставки",
         "LIST_COLUMN_LABEL": "Адрес доставки",
         "USER_TYPE_ID": "string",
         "XML_ID": "DELIVERY_ADRESS"
         },
        {"FIELD_NAME": "DELIVERY_DATE",
         "ALT_FIELD_NAME_BX24": "UF_CRM_DELIVERY_DATE",
         "EDIT_FORM_LABEL": "Дата доставки",
         "LIST_COLUMN_LABEL": "Дата доставки",
         "USER_TYPE_ID": "string",
         "XML_ID": "DELIVERY_DATE"
         },
        {"FIELD_NAME": "DELIVERY_CODE",
         "ALT_FIELD_NAME_BX24": "UF_CRM_DELIVERY_CODE",
         "EDIT_FORM_LABEL": "Код доставки",
         "LIST_COLUMN_LABEL": "Код доставки",
         "USER_TYPE_ID": "string",
         "XML_ID": "DELIVERY_CODE"
         },
    ]

    date_pattern = '(?:2[0-9][2-9][0-9])-(?:0?[1-9]|[12][0-9]|3[01])-(?:0?[1-9]|1[0-2]):(?:0?[1-9]|[1][0-9]|2[0-3]):(?:0?[0-9]|[0-5][0-9])'

    fields_request = {
        'title': '.*',
        'description': '.*',
        'products': list,
        'delivery_adress': '.*',
        'delivery_date': date_pattern,
        "delivery_code": '#.*',
        "client": {
            "name": '.*',
            "surname": '.*',
            "phone": '^(7|8|\+7)(\d{3})(\d{7})$',
            "adress": '.*'
        }
    }


@web_app.route(url_to_request, methods=['POST'])
def post_deal():
    deal = request.json
    check_result = check_fields_in_request(deal)
    if check_result['code'] != 200:
        return jsonify(check_result['description']), check_result['code']
    response = create_or_update_b24_deal(deal)
    return jsonify(response['data']), response['code']


def check_fields_in_request(request_dict: dict) -> dict:
    """
    Checks if all fields in request is correct

    :return: if not correct returns dict with description of error and error code like
            {'description': 'Can't find some field', 'code': 400},
            else fields are correct return dict, like {'description': 'ok', 'code': True}
    """
    pattern = Fields.fields_request
    for key, value in request_dict.items():
        if key not in pattern:
            error_str = key + ' a field with this name is not allowed'
            error_code = 400
            return {'description': error_str, 'code': error_code}
        if key == 'client':
            for key2level, value2level in value.items():
                if key2level not in pattern['client']:
                    error_str = key2level + ' in structure "client" a field with this name is not allowed'
                    error_code = 400
                    return {'description': error_str, 'code': error_code}

                if not re.fullmatch(pattern['client'][key2level], value2level):
                    error_str = key2level + ' wrong format'
                    error_code = 400
                    return {'description': error_str, 'code': error_code}

        if key == 'products':
            if not isinstance(value, list):
                return {'description': 'field "products" is not List', 'code': 400}

        elif key != 'client':

            if not re.match(pattern[key], value):
                error_str = key + ' wrong format'
                error_code = 400
                return {'description': error_str, 'code': error_code}

    return {'description': 'ok', 'code': 200}


def get_request():
    pass


def get_deal() -> dict:
    """
    gets the deal from rest response and transform it in dict, then return it
    :return: dict
    """
    get_request()
    pass


def deal_exist(delivery_code):
    """
    Check if deal already exist. If exist return True, else False
    :return: bool
    """

    return False


def client_exist(phone):
    """
    Check if client exist. If client exist return True, else False
    :return: bool
    """
    client = bx24.callMethod("crm.contact.list", filter={"PHONE": phone}, select=["ID", "NAME", "LAST_NAME"])

    if client:
        return client

    return False


def create_client(client):
    """
    Creates client. If created successful return True, else False
    :return: bool
    """
    fields = {"NAME": client['name'],
              "LAST_NAME": client['surname'],
              "OPENED": "Y",
              "TYPE_ID": "CLIENT",
              "ADDRESS": client['address'],
              "PHONE": [{"VALUE": client['phone'], "VALUE_TYPE": "HOME"}]}
    response = bx24.callMethod("crm.contact.add", fields=fields)
    print(response)
    return response


def create_deal(deal_request):
    """
    Creates client if it doesn't exist, create deal.
    :return:
    """
    pass


def update_deal(deal_request):
    """
    Updates the deal if it exists
    :return:
    """
    pass


def create_or_update_deal(deal_request: dict):
    """
    Create in Bitrix24 client if not exist and create deal, if client exist create just deal, else
    if any changes update deal.
    :param deal_request: dict
    :return: None
    """
    if deal_exist(deal_request['delivery_code']):
        create_deal(deal_request)
    else:
        update_deal(deal_request)


def create_or_update_b24_deal(deal_request):
    """
    function gets and creates deal and client, if not exists, else update deal
    :return:
    """
    phone = deal_request['client']['phone']
    found_client = client_exist(phone)
    if found_client:
        deal_request['found_client'] = found_client[0]
        create_or_update_deal(deal_request)
        response = {'data': deal_request, 'code': 200}
        return response
    else:
        create_client(deal_request['client'])
        create_deal(deal_request)
        response = {'data': deal_request, 'code': 201}
        return response


def check_fields_in_bx24():

    deal_fields = bx24.callMethod("crm.deal.userfield.list")
    list_of_deal_fields = []
    for deal_field in deal_fields:
        list_of_deal_fields.append(deal_field['FIELD_NAME'])

    for curr_field in Fields.fields_bx24:
        if curr_field['ALT_FIELD_NAME_BX24'] not in list_of_deal_fields:
            bx24.callMethod("crm.deal.userfield.add", fields=curr_field)


def temp_del_fields_from_bx24() -> None:
    """
    Временная функция для удаления полей в Bitrix24.
    :return: None
    """
    fields_to_delete = ['UF_CRM_DESCRIPTION', 'UF_CRM_PRODUCTS', 'UF_CRM_DELIVERY_ADRESS', 'UF_CRM_DELIVERY_DATE',
                        'UF_CRM_DELIVERY_CODE']
    deal_fields = bx24.callMethod("crm.deal.userfield.list")
    for curr_field in deal_fields:
        if curr_field['FIELD_NAME'] in fields_to_delete:
            bx24.callMethod("crm.deal.userfield.delete", id=curr_field['ID'])


if __name__ == '__main__':

    check_fields_in_bx24()

    web_app.run()
