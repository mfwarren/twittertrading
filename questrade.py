import json
import os
import requests


# http://www.questrade.com/api/documentation/rest-operations/order-calls/accounts-id-orders

URL_BASE = "https://login.questrade.com"

DEBUG = True


class Order(object):
    def __init__(self, account_number, symbol_id, quantity, iceberg_quantity,
                 limit_price=None, stop_price=None, is_all_or_none=True, is_anonymous=False, order_type='Limit',
                 time_in_force='GoodTillCancelled', action='Buy', primary_route='AUTO',
                 secondary_route='AUTO'):
        self.account_number = account_number
        self.symbol_id = symbol_id
        self.quantity = quantity
        self.iceberg_quantity = iceberg_quantity
        self.limit_price = limit_price
        self.stop_price = stop_price
        self.is_all_or_none = is_all_or_none
        self.is_anonymous = is_anonymous
        self.order_type = order_type
        self.time_in_force = time_in_force
        self.action = action
        self.primary_route = primary_route
        self.secondary_route = secondary_route

    @property
    def params(self):
        return {
            'symbolId': self.symbol_id,
            'quantity': self.quantity,
            'icebergQuantity': self.iceberg_quantity,
            'limitPrice': self.limit_price,
            'stopPrice': self.stop_price,
            'is_all_or_none': self.is_all_or_none,
            'is_anonymous': self.is_anonymous,
            'order_type': self.order_type,
            'time_in_force': self.time_in_force,
            'action': self.action,
            'primary_route': self.primary_route,
            'secondary_route': self.secondary_route}


class QuestradeClient(object):
    def __init__(self, refresh_token=None):
        if os.path.exists('questrade_auth.json'):
            with open('questrade_auth.json') as auth_file:
                data = json.load(auth_file)
                self.token_type = data['token_type']
                self.access_token = data['access_token']
                self.refresh_token = data['refresh_token']
                self.api_server = data['api_server']
        else:
            self.token_type = None
            self.access_token = None
            self.refresh_token = refresh_token
            self.api_server = None

    def update_token(self, info):
        self.token_type = info['token_type']
        self.access_token = info['access_token']
        self.refresh_token = info['refresh_token']
        self.api_server = info['api_server']

        with open('questrade_auth.json', 'w') as auth_file:
            auth_file.write(json.dumps({'token_type': self.token_type,
                                        'access_token': self.access_token,
                                        'refresh_token': self.refresh_token,
                                        'api_server': self.api_server}))

    def auth_headers(self):
        if self.access_token is None:
            self.get_tokens()
        return {"Authorization": f'{self.token_type} {self.access_token}'}

    def get_tokens(self):
        refresh_url = "/oauth2/token?grant_type=refresh_token&refresh_token="
        if self.refresh_token is None:
            print("Expired refresh key.")
            print("Go to: " + URL_BASE + "/Signin.aspx?ReturnUrl=%2fAPIAccess%2fUserApps.aspx")
            response = requests.get(URL_BASE + refresh_url + input("Please enter your new refresh key: "))
            self.update_token(response.json())
        else:
            print(URL_BASE + refresh_url + self.refresh_token)
            response = requests.get(URL_BASE + refresh_url + self.refresh_token)
            print(response.text)
            self.update_token(response.json())

    def get(self, url, headers=None, params=None):
        if self.api_server is None:
            self.get_tokens()
        response = requests.get(self.api_server + url, headers=headers, params=params)
        if 'code' in response.json() and response.json()['code'] == 1017:
            self.get_tokens()
            response = requests.get(self.api_server + url, headers=headers, params=params)
        return response.json()

    def create_order(self, order):
        print('Making Trade')
        print(order.params)
        if not DEBUG:
            response = requests.post('v1/accounts/{order.account_number}/orders', headers=self.auth_headers(), params=order.params)
            print(response.text())
            return response.json()

    def get_accounts(self):
        return self.get('v1/accounts', headers=self.auth_headers())

    def get_symbol(self, prefix, offset=0):
        matches = self.get('v1/symbols/search', headers=self.auth_headers(), params={'prefix': prefix, 'offset': offset})
        for m in matches.get('symbols', []):
            if m['symbol'] == prefix:
                return m
        return None

