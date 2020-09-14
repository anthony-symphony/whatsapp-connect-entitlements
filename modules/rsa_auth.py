import datetime
from jose import jwt

class SymBotRSAAuth():
    """Class for RSA authentication"""

    def __init__(self, config):
        """
        Set up proxy information if configuration contains proxyURL
        :param config: Object contains all RSA configurations
        """
        self.config = config


    def create_jwt(self, entitlementType):
        with open(self.config.data['botRSAPath'], 'r') as f:
            content = f.readlines()
            private_key = ''.join(content)
            current_date = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
            expiration_date = current_date + (5*58)

            if entitlementType == 'WHATSAPP':
                payload = {
                    'sub': 'ces:customer:' + self.config.data['publicKeyId'],
                    'exp': expiration_date,
                    'iat': current_date
                }
            elif entitlementType == 'WECHAT':
                payload = {
                    'sub': 'ces:customer:' + self.config.data['publicKeyId'] + ':' + self.config.data['podId'],
                    'exp': expiration_date,
                    'iat': current_date
                }

            encoded = jwt.encode(payload, private_key, algorithm='RS512')
            f.close()
            return encoded
