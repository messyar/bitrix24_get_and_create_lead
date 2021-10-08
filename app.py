from bitrix24 import Bitrix24, BitrixError
import requests


def get_lead() -> dict:
    """
    gets the lead from rest response and transform it in dict, then return it
    :return: dict
    """
    pass


def lead_exist():
    """
    Check if lead already exist. If exist return True, else False
    :return: bool
    """
    pass


def client_exist():
    """
    Check if client exist. If client exist return True, else False
    :return: bool
    """
    pass


def create_client():
    """
    Creates client. If created successful return True, else False
    :return: bool
    """
    pass


def create_lead():
    """
    Creates client if it doesn't exist, create lead.
    :return:
    """
    if client_exist():
        pass
    else:
        create_client()


def update_lead():
    """
    Updates the lead if it exists
    :return:
    """
    pass


def create_or_update_lead(lead: dict):
    """
    Create in Bitrix24 client if not exist and create lead, if client exist create just lead, else
    if any changes update lead.
    :param lead: dict
    :return: None
    """
    if lead_exist():
        create_lead()
    else:
        update_lead()


def get_and_create_or_update_b24_lead():
    """
    function gets and creates lead and client, if not exists, else update lead
    :return:
    """
    lead = get_lead()
    create_or_update_lead(lead)


if __name__ == '__main__':
    get_and_create_or_update_b24_lead()
