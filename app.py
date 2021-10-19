from bitrix24 import Bitrix24, BitrixError
import requests
from flask import Flask, jsonify, request
from os import environ
from pprint import pprint
import re

# declaration of global variable
web_app = Flask(__name__)

# try to get url with API key from environment variable
try:
    api_key = environ['API_KEY']
    url_to_request = '/deal/' + api_key + '/'
except Exception as name_error:
    print("Can't find Environment variable %s" % name_error)

try:
    url_to_b24 = environ['URL_TO_B24']
    # creating instance of Bitrix24 class
    bx24 = Bitrix24(url_to_b24)
except Exception as name_error:
    print("Can't find Environment variable %s" % name_error)


# Class with structure of fields in request and in Bitrix24
class Fields:
    fields_bx24 = {"DESCRIPTION":
                       {"FIELD_NAME": "DESCRIPTION",
                        "ALT_FIELD_NAME_BX24": "UF_CRM_DESCRIPTION",
                        "EDIT_FORM_LABEL": "Описание",
                        "LIST_COLUMN_LABEL": "Описание",
                        "USER_TYPE_ID": "string",
                        "XML_ID": "DESCRIPTION"
                        },
                   "PRODUCTS":
                       {"FIELD_NAME": "PRODUCTS",
                        "ALT_FIELD_NAME_BX24": "UF_CRM_PRODUCTS",
                        "EDIT_FORM_LABEL": "Продукты",
                        "LIST_COLUMN_LABEL": "Продукты",
                        "USER_TYPE_ID": "string",
                        "XML_ID": "PRODUCTS"
                        },
                   "DELIVERY_ADRESS":
                       {"FIELD_NAME": "DELIVERY_ADRESS",
                        "ALT_FIELD_NAME_BX24": "UF_CRM_DELIVERY_ADRESS",
                        "EDIT_FORM_LABEL": "Адрес доставки",
                        "LIST_COLUMN_LABEL": "Адрес доставки",
                        "USER_TYPE_ID": "string",
                        "XML_ID": "DELIVERY_ADRESS"
                        },
                   "DELIVERY_DATE":
                       {"FIELD_NAME": "DELIVERY_DATE",
                        "ALT_FIELD_NAME_BX24": "UF_CRM_DELIVERY_DATE",
                        "EDIT_FORM_LABEL": "Дата доставки",
                        "LIST_COLUMN_LABEL": "Дата доставки",
                        "USER_TYPE_ID": "string",
                        "XML_ID": "DELIVERY_DATE"
                        },
                   "DELIVERY_CODE":
                       {"FIELD_NAME": "DELIVERY_CODE",
                        "ALT_FIELD_NAME_BX24": "UF_CRM_DELIVERY_CODE",
                        "EDIT_FORM_LABEL": "Код доставки",
                        "LIST_COLUMN_LABEL": "Код доставки",
                        "USER_TYPE_ID": "string",
                        "XML_ID": "DELIVERY_CODE"
                        },
                   }

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


def serialize_deal(dict_to_serialize: dict) -> dict:
    """
    Serialize request to format to add
    :param dict_to_serialize: dict
    :return: serialized dict
    """
    serialized_dict = {}
    for key in dict_to_serialize:
        if key == 'client':
            continue

        serialized_key = key.upper()
        if serialized_key in Fields.fields_bx24:
            serialized_key = Fields.fields_bx24[serialized_key]["ALT_FIELD_NAME_BX24"]
        serialized_dict[serialized_key] = dict_to_serialize[key]
        if key == 'delivery_code':
            serialized_dict[serialized_key] = dict_to_serialize[key].replace('#', '%23')
        if key == 'products':
            serialized_dict[serialized_key] = ', '.join(dict_to_serialize[key])

    return serialized_dict


@web_app.route(url_to_request, methods=['POST', 'PUT', 'PATCH'])
def post_deal():
    """
    Post request processing function
    :return:
    """
    deal = request.json
    # check if fields in request correct
    check_result = check_fields_in_request(deal)
    # if fields in request not correct, send response with code 400 and descriptions of error
    if check_result['code'] != 200:
        return jsonify(check_result['description']), check_result['code']
    # try to create or update deal if exists
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


def deal_exist(delivery_code):
    """
    Check if deal already exist. If exist return True, else False
    :return: bool
    """

    select_fields = ['ID', 'CONTACT_ID', 'TITLE', 'UF_CRM_DESCRIPTION', 'UF_CRM_PRODUCTS', 'UF_CRM_DELIVERY_ADRESS',
                     'UF_CRM_DELIVERY_DATE', 'UF_CRM_DELIVERY_CODE']
    delivery_code = delivery_code.replace('#', '%23')
    found_deal = bx24.callMethod("crm.deal.list", filter={"UF_CRM_DELIVERY_CODE": delivery_code},
                                 select=select_fields)
    if found_deal:
        return found_deal[0]
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
              "ADDRESS": client['adress'],
              "PHONE": [{"VALUE": client['phone'], "VALUE_TYPE": "HOME"}]}
    response = bx24.callMethod("crm.contact.add", fields=fields)
    return response


def create_deal(deal_request):
    """
    Creates client if it doesn't exist, create deal.
    :return:
    """
    serialized_deal = serialize_deal(deal_request)
    bx24.callMethod("crm.deal.add", fields=serialized_deal)
    pass


def update_deal(deal_request, deal_found):
    """
    Compare fields in found deal with deal in request and updates the deal if necessary
    :return: dict
    """
    serialized_deal = serialize_deal(deal_request)
    changed_fields = {}
    if deal_request['CONTACT_ID'] != deal_found['CONTACT_ID']:
        return {'data': 'The client found in the request differs from the one saved'
                        ' in the application in Bitrix 24.',
                'code': 400}
    for key, value in serialized_deal.items():
        if key == 'UF_CRM_DELIVERY_CODE':
            continue

        if serialized_deal[key] != deal_found[key]:
            changed_fields[key] = serialized_deal[key]

    bx24.callMethod("crm.deal.update", id=deal_found['ID'], fields=changed_fields)

    if changed_fields:
        changed_fields_descr = 'Changed fields: ' + str(changed_fields)
    else:
        changed_fields_descr = 'Request is equal to application. No changes was made.'

    return {'data': changed_fields_descr, 'code': 200}


def create_or_update_deal(deal_request: dict):
    """
    Create in Bitrix24 client if not exist and create deal, if client exist create just deal, else
    if any changes update deal.
    :param deal_request: dict
    :return: None
    """
    deal_found = deal_exist(deal_request['delivery_code'])
    if deal_found:
        return update_deal(deal_request, deal_found)
    else:
        create_deal(deal_request)


def create_or_update_b24_deal(deal_request):
    """
    function gets and creates deal and client, if not exists, else update deal
    :param: deal_request: dict
    :return: response as dict
    """
    phone = deal_request['client']['phone']
    found_client = client_exist(phone)
    deal = deal_request.copy()
    if found_client:
        deal['CONTACT_ID'] = found_client[0]['ID']
        code = 200
    else:
        code = 201
        id_new_client = create_client(deal_request['client'])
        deal['CONTACT_ID'] = id_new_client

    response = create_or_update_deal(deal)
    if not response:
        response = {'data': deal_request, 'code': code}
    return response


def check_fields_in_bx24() -> None:
    """
    Check if necessary fields exists in Bitrix24, if not exists creates it
    :return: None
    """
    deal_fields = []
    try:
        deal_fields = bx24.callMethod("crm.deal.userfield.list")

    except BitrixError as message:
        if message.args[0] == 'Invalid request credentials':
            print(message)
            print("Possible it wrong url to API, or can't reach url. Please set correct Environment"
                  "variable named 'URL_TO_B24' with url to API, or check connection.")

    list_of_deal_fields = []
    for deal_field in deal_fields:
        list_of_deal_fields.append(deal_field['FIELD_NAME'])

    for curr_field in Fields.fields_bx24:
        if Fields.fields_bx24[curr_field]['ALT_FIELD_NAME_BX24'] not in list_of_deal_fields:
            field_to_add = Fields.fields_bx24[curr_field]
            field_to_add.pop('ALT_FIELD_NAME_BX24')
            bx24.callMethod("crm.deal.userfield.add", fields=field_to_add)


if __name__ == '__main__':
    check_fields_in_bx24()
    print('The service for receiving applications from the site and redirecting to Bitrix24 has been launched')
    web_app.run()
