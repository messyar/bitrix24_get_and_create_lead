from bitrix24 import Bitrix24, BitrixError
from flask import Flask, jsonify, request
from os import environ
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

    date_pattern = '^(?:2[0-9][2-9][0-9])-(?:0?[1-9]|[12][0-9]|3[01])-(?:0?[1-9]|1[0-2]):(?:0?[1-9]|[1][0-9]|2[0-3]):(?:0?[0-9]|[1-5][1-9])$'

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
    Serialize request to format for Bitrix24
    :param dict_to_serialize: dict
    :return: serialized dict, if dict_to_serialized is dict, else False
    """

    if not isinstance(dict_to_serialize, dict):
        return False

    serialized_dict = {}
    for key in dict_to_serialize:
        if key == 'client':
            continue

        serialized_key = key.upper()
        if serialized_key in Fields.fields_bx24:
            serialized_key = Fields.fields_bx24[serialized_key]["ALT_FIELD_NAME_BX24"]
        serialized_dict[serialized_key] = dict_to_serialize[key]
        if key == 'delivery_code':
            # need to replace the symbol # in UTF-8 hex code, otherwise it is parsed
            # as an empty string in Bitrix24
            serialized_dict[serialized_key] = dict_to_serialize[key].replace('#', '%23')
        if key == 'products':
            serialized_dict[serialized_key] = ', '.join(dict_to_serialize[key])

    return serialized_dict


@web_app.route(url_to_request, methods=['POST', 'PUT', 'PATCH'])
def post_deal() -> None:
    """
    Post request processing function
    :return: response
    """
    deal = request.json
    # check if fields in request correct
    check_result = check_fields_in_request(deal)
    # if fields in request not correct, send response with code 400 and descriptions of error
    if check_result['code'] != 200:
        return jsonify(check_result['data']), check_result['code']
    # try to create or update deal if exists
    response = create_or_update_b24_deal(deal)
    return jsonify(response['data']), response['code']


def check_fields_in_request(request_dict: dict) -> dict:
    """
    Checks if all fields in request is correct
    :param request_dict: dict
    :return: if not correct returns dict with description of error and error code like
            {'description': 'Can't find some field', 'code': 400},
            else fields are correct return dict, like {'description': 'ok', 'code': 200}
    """
    pattern = Fields.fields_request
    error_code = 400
    if 'client' not in request_dict:
        error_str = ' the field with the name client was not found in request'
        return {'data': error_str, 'code': error_code}

    for key, value in pattern.items():
        if key not in request_dict:
            error_str = ' the field with the name {} was not found in request'.format(key)

            return {'data': error_str, 'code': error_code}
        if key == 'client':
            for key2level, value2level in value.items():
                if key2level not in request_dict['client']:
                    error_str = key2level + ' in structure "client" the field with the name {} ' \
                                            'was not found in request'.format(key)
                    return {'data': error_str, 'code': error_code}

                if not re.match(value2level, request_dict['client'][key2level]):
                    error_str = key2level + ' wrong format'
                    return {'data': error_str, 'code': error_code}

        if key == 'products':
            if not isinstance(request_dict[key], list):
                return {'data': 'field "products" is not List', 'code': error_code}

        elif key != 'client':

            if not re.match(value, request_dict[key]):
                error_str = key + ' wrong format'
                return {'data': error_str, 'code': error_code}

    return {'data': 'ok', 'code': 200}


def deal_exist(delivery_code: dict) -> dict:
    """
    Check if deal already exists. If exist return True, else False
    :param delivery_code: dict
    :return: False, if deal not exists, else return found deal
    """

    select_fields = ['ID', 'CONTACT_ID', 'TITLE', 'UF_CRM_DESCRIPTION', 'UF_CRM_PRODUCTS', 'UF_CRM_DELIVERY_ADRESS',
                     'UF_CRM_DELIVERY_DATE', 'UF_CRM_DELIVERY_CODE']
    # need to replace the symbol # in UTF-8 hex code, otherwise it is parsed
    # as an empty string in Bitrix24
    delivery_code = delivery_code.replace('#', '%23')
    found_deal = bx24.callMethod("crm.deal.list", filter={"UF_CRM_DELIVERY_CODE": delivery_code},
                                 select=select_fields)
    if found_deal:
        return found_deal[0]
    return False


def client_exist(phone: str) -> dict:
    """
    Check if client exist. If client exist return True, else False
    :param phone: str
    :return: False, if client doesn't exists, else return found client
    """
    client = bx24.callMethod("crm.contact.list", filter={"PHONE": phone}, select=["ID", "NAME", "LAST_NAME"])

    if client:
        return client

    return False


def create_client(client: dict) -> dict:
    """
    Creates client in Bitrix24
    :param client: dict
    :return: response
    """
    fields = {"NAME": client['name'],
              "LAST_NAME": client['surname'],
              "OPENED": "Y",
              "TYPE_ID": "CLIENT",
              "ADDRESS": client['adress'],
              "PHONE": [{"VALUE": client['phone'], "VALUE_TYPE": "HOME"}]}
    response = bx24.callMethod("crm.contact.add", fields=fields)
    return response


def create_deal(deal_request: dict) -> dict:
    """
    Creates deal in Bitrix24
    :param deal_request: dict
    :return:
    """
    # serialize deal in for sending in Bitrix24 with right format
    serialized_deal = serialize_deal(deal_request)
    bx24.callMethod("crm.deal.add", fields=serialized_deal)


def update_deal(deal_request, deal_found) -> dict:
    """
    Compare fields in found deal with deal in request and updates the deal if necessary
    :param deal_request: dict
    :param deal_found: dict
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
    result_of_check = check_fields_in_request(deal_request)
    if result_of_check['code'] == 400:
        return result_of_check

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
    flask_port = ''
    try:
        flask_port = environ['PORT']

    except Exception as name_error:
        print("Can't find Environment variable %s" % name_error)

    flask_port = int(flask_port)
    print('The service for receiving applications from the site and redirecting to Bitrix24 has been launched'
          ' on port: ', flask_port)
    from waitress import serve

    serve(web_app, host="0.0.0.0", port=flask_port)
