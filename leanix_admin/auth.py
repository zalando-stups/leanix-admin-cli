import requests
import requests.auth as requests_auth


class LeanixAuth(requests_auth.AuthBase):
    def __init__(self, api_token, oauth_token_url):
        self.oauth_token_url = oauth_token_url
        self.api_token = api_token
        self.access_token = None

    def obtain_access_token(self):
        if not self.access_token:
            response = requests.post(self.oauth_token_url,
                                     data={'grant_type': 'client_credentials'},
                                     auth=('apitoken', self.api_token))
            response.raise_for_status()
            self.access_token = response.json()['access_token']
        return self.access_token

    def auth_header(self):
        return 'Bearer ' + self.obtain_access_token()

    def __call__(self, r):
        r.headers['Authorization'] = self.auth_header()
        return r
