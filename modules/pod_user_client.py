from sym_api_client_python.configure.configure import SymConfig
from sym_api_client_python.auth.rsa_auth import SymBotRSAAuth
from sym_api_client_python.clients.sym_bot_client import SymBotClient
from sym_api_client_python.clients.admin_client import AdminClient



class PodUserClient():

    def __init__(self, appId):
        # RSA Auth flow: pass path to rsa config.json file
        configure = SymConfig('./resources/symphony_config.json')
        configure.load_config()
        auth = SymBotRSAAuth(configure)
        auth.authenticate()

        # Initialize SymBotClient with auth and configure objects
        self.bot_client = SymBotClient(auth, configure)
        self.admin_client = AdminClient(self.bot_client)
        self.email_dict, self.username_dict = self.get_all_active_users()
        self.appId = appId


    def get_all_active_users(self):
        output = self.admin_client.admin_list_users(skip=0, limit=1000)

        while True:
            next_out = self.admin_client.admin_list_users(skip=int(len(output)), limit=1000)
            if len(next_out) > 0:
                for index in range(len(next_out)): output.append(next_out[index])
            else:
                break

        # Filter out Disabled users and create Dictionary
        email_dict = dict()
        username_dict = dict()
        for u in output:
            if u["userSystemInfo"]["status"] == "ENABLED":
                email = u['userAttributes']['emailAddress']
                username = u['userAttributes']['userName']
                user_id = u['userSystemInfo']['id']

                email_dict[email] = user_id
                username_dict[username] = user_id

        return email_dict, username_dict

    def install_connect_app_by_userid(self, user_id):
        output = self.admin_get_user_features(user_id)
        is_updated = False

        for o in output:
            if o["appId"] == self.appId and o['install'] == False:
                o['install'] = True
                is_updated = True
                break

        if is_updated:
            self.admin_update_user_features(user_id, output)

        return is_updated


    def remove_connect_app_by_userid(self, user_id):
        output = self.admin_get_user_features(user_id)
        is_updated = False

        for o in output:
            if o["appId"] == self.appId and o['install'] == True:
                o['install'] = False
                is_updated = True
                break

        if is_updated:
            self.admin_update_user_features(user_id, output)

        return is_updated


    def admin_get_user_features(self, user_id):
        url = '/pod/v1/admin/user/{0}/app/entitlement/list'.format(user_id)
        return self.bot_client.execute_rest_call("GET", url)


    def admin_update_user_features(self, user_id, app_list):
        url = '/pod/v1/admin/user/{0}/app/entitlement/list'.format(user_id)
        return self.bot_client.execute_rest_call("POST", url, json=app_list)


    def lookup_user_by_email(self, emailAddress):
        if emailAddress in self.email_dict:
            return self.email_dict[emailAddress]

        return None
