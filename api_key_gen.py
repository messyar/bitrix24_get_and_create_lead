import random

big = 'QWERTYUIOPASDFGHJKLZXCVBNM'
low = 'qwertyuiopasdfghjklzxcvbnm'
num = '1234567890.'

api_key_dict = big + low + num
api_key_len = 40


def api_key_gen():
    result_password = ''.join([random.choice(api_key_dict) for x in range(api_key_len)])
    return result_password


print(api_key_gen())
