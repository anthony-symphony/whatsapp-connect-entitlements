import requests
import json
from json.decoder import JSONDecodeError


class EntitlementClient():

    def __init__(self, auth, config, connect_app):
        self.auth = auth
        self.config = config

        if connect_app == 'WHATSAPP':
            self.entitlementType = 'WHATSAPPGROUPS'
        elif connect_app == 'WECHAT':
            self.entitlementType = 'WECHAT'

    def list_entitlements(self):
        if self.entitlementType == 'WHATSAPPGROUPS':
            url = '/admin/api/v1/customer/entitlements'
        elif self.entitlementType == 'WECHAT':
            url = '/wechatgateway/api/v1/entitlements'

        user_list = []
        output = self.execute_rest_call("GET", url)

        if self.entitlementType == 'WHATSAPPGROUPS':
            while 'entitlements' in output and len(output['entitlements']) > 0:
                user_list = user_list + output['entitlements']

                if 'pagination' in output:
                    if 'next' in output['pagination']:
                        next_url = url + output['pagination']['next']
                        output = self.execute_rest_call("GET", next_url)
                    else:
                        output = dict()
        elif self.entitlementType == 'WECHAT':
            user_list = user_list + output

        return user_list


    def add_entitlements(self, user_id):
        if self.entitlementType == 'WHATSAPPGROUPS':
            url = '/admin/api/v1/customer/entitlements'
        elif self.entitlementType == 'WECHAT':
            url = '/wechatgateway/api/v1/entitlements'

        body = {
            "entitlementType": self.entitlementType,
            "symphonyId": str(user_id)
        }

        return self.execute_rest_call("POST", url, json=body)


    def get_entitlements(self, user_id):
        if self.entitlementType == 'WHATSAPPGROUPS':
            url = f'/admin/api/v1/customer/entitlements/{str(user_id)}/entitlementType/{self.entitlementType}'
        elif self.entitlementType == 'WECHAT':
            url = f'/wechatgateway/api/v1/entitlements/{str(user_id)}/entitlementType/{self.entitlementType}'

        return self.execute_rest_call("GET", url)


    def delete_entitlements(self, user_id):
        if self.entitlementType == 'WHATSAPPGROUPS':
            url = f'/admin/api/v1/customer/entitlements/{str(user_id)}/entitlementType/{self.entitlementType}'
        elif self.entitlementType == 'WECHAT':
            url = f'/wechatgateway/api/v1/entitlements/{str(user_id)}/entitlementType/{self.entitlementType}'

        return self.execute_rest_call("DELETE", url)


    def get_session(self):
        session = requests.Session()
        session.headers.update({
            'Content-Type': "application/json",
            'Authorization': "Bearer " + self.auth.create_jwt(self.entitlementType)}
        )

        session.proxies.update(self.config.data['proxyRequestObject'])
        if self.config.data["truststorePath"]:
            print("Setting truststorePath to {}".format(
                self.config.data["truststorePath"])
            )
            session.verify = self.config.data["truststorePath"]

        return session


    def execute_rest_call(self, method, path, **kwargs):
        results = None
        url = self.config.data['apiURL'] + path
        session = self.get_session()
        try:
            response = session.request(method, url, **kwargs)
        except requests.exceptions.ConnectionError as err:
            print(err)
            print(type(err))
            raise

        if response.status_code == 204:
            results = []
        elif response.status_code in (200, 409, 201, 404, 400):
            try:
                results = json.loads(response.text)
            except JSONDecodeError:
                results = response.text
        else:
            # Try to get the json to be used to handle the error message
            print('Failed while invoking ' + url)
            print('Status Code: ' + str(response.status_code))
            print('Response: ' + response.text)
            raise Exception(response.text)

        return results