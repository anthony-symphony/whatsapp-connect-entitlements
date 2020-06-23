import requests
import json
from json.decoder import JSONDecodeError


class EntitlementClient():

    def __init__(self, auth, config):
        self.auth = auth
        self.config = config


    def list_entitlements(self):
        #url = '/admin/api/v1/entitlements'
        url = '/admin/api/v1/customer/entitlements'
        return self.execute_rest_call("GET", url)


    def add_entitlements(self, user_id):
        #url = '/admin/api/v1/entitlements'
        url = '/admin/api/v1/customer/entitlements'

        body = {
            "entitlementType": "WHATSAPPGROUPS",
            "symphonyId": str(user_id)
        }

        return self.execute_rest_call("POST", url, json=body)


    def get_entitlements(self, user_id):
        #url = f'/admin/api/v1/entitlements/{str(user_id)}/entitlementType/WHATSAPPGROUPS'
        url = f'/admin/api/v1/customer/entitlements/{str(user_id)}/entitlementType/WHATSAPPGROUPS'
        return self.execute_rest_call("GET", url)


    def delete_entitlements(self, user_id):
        #url = f'/admin/api/v1/entitlements/{str(user_id)}/entitlementType/WHATSAPPGROUPS'
        url = f'/admin/api/v1/customer/entitlements/{str(user_id)}/entitlementType/WHATSAPPGROUPS'

        return self.execute_rest_call("DELETE", url)


    def get_session(self):
        session = requests.Session()
        session.headers.update({
            'Content-Type': "application/json",
            'Authorization': "Bearer " + self.auth.create_jwt()}
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
        url = self.config.data['sessionAuthHost'] + path
        session = self.get_session()

        try:
            response = session.request(method, url, **kwargs)
        except requests.exceptions.ConnectionError as err:
            print(err)
            print(type(err))
            raise

        if response.status_code == 204:
            results = []
        elif response.status_code in (200, 409, 201, 404):
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