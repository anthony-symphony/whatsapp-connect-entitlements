import requests
import json
from json.decoder import JSONDecodeError


class EntitlementClient():

    def __init__(self, auth, config, connect_app):
        self.auth = auth
        self.config = config
        self.jwt = None

        if connect_app == 'WHATSAPP':
            self.entitlementType = 'WHATSAPP'
        elif connect_app == 'WECHAT':
            self.entitlementType = 'WECHAT'

    def list_entitlements(self):
        if self.entitlementType == 'WHATSAPP':
            url = f'/admin/api/v1/customer/entitlements/externalNetwork/{self.entitlementType}/advisors'
        elif self.entitlementType == 'WECHAT':
            url = f'/wechatgateway/api/v1/customer/entitlements/externalNetwork/{self.entitlementType}/advisors'

        user_list = []
        output = self.execute_rest_call("GET", url)

        while 'entitlements' in output and len(output['entitlements']) > 0:
            user_list = user_list + output['entitlements']

            if 'pagination' in output:
                if 'next' in output['pagination'] and output['pagination']['next'] is not None:
                    next_url = url + output['pagination']['next']
                    output = self.execute_rest_call("GET", next_url)
                else:
                    output = dict()
            else:
                output = dict()

        return user_list


    def add_entitlements(self, user_id):
        if self.entitlementType == 'WHATSAPP':
            url = '/admin/api/v2/customer/entitlements'
        elif self.entitlementType == 'WECHAT':
            url = '/wechatgateway/api/v2/customer/entitlements'

        body = {
            "externalNetwork": self.entitlementType,
            "symphonyId": str(user_id)
        }

        return self.execute_rest_call("POST", url, json=body)


    def add_room_permission(self, user_email):
        if self.entitlementType == 'WHATSAPP':
            url = f'/admin/api/v1/customer/advisors/emailAddress/{user_email}/externalNetwork/{self.entitlementType}/permissions'
        elif self.entitlementType == 'WECHAT':
            url = f'/wechatgateway/api/v1/customer/advisors/advisorEmailAddress/{user_email}/externalNetwork/{self.entitlementType}/permissions'

        body = {
            "advisorEmailAddress": [user_email],
            "externalNetwork": self.entitlementType,
            "permissionName": "create:room"
        }

        return self.execute_rest_call("POST", url, json=body)


    def get_entitlements(self, user_id):
        if self.entitlementType == 'WHATSAPP':
            url = f'/admin/api/v2/customer/advisor/entitlements?advisorSymphonyId={user_id}&externalNetwork={self.entitlementType}'
        elif self.entitlementType == 'WECHAT':
            url = f'/wechatgateway/api/v2/customer/advisor/entitlements?advisorSymphonyId={user_id}&externalNetwork={self.entitlementType}'

        return self.execute_rest_call("GET", url)


    def delete_entitlements(self, user_id):
        if self.entitlementType == 'WHATSAPP':
            url = f'/admin/api/v2/customer/advisor/entitlements?advisorSymphonyId={user_id}&externalNetwork={self.entitlementType}'
        elif self.entitlementType == 'WECHAT':
            url = f'/wechatgateway/api/v2/customer/advisor/entitlements?advisorSymphonyId={user_id}&externalNetwork={self.entitlementType}'

        return self.execute_rest_call("DELETE", url)


    def get_session(self):
        session = requests.Session()

        if self.jwt is not None:
            jwt = self.jwt
        else:
            jwt = self.auth.create_jwt(self.entitlementType)

        session.headers.update({
            'Content-Type': "application/json",
            'Authorization': "Bearer " + jwt}
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
        # JWT Expired - Generate new one
        elif response.status_code == 401:
            print("JWT Expired - Reauthenticating...")
            self.jwt = None
            return self.execute_rest_call(method, path, **kwargs)
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
