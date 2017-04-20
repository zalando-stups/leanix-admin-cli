import jwt
import requests
import requests.auth as requests_auth
import logging
import leanix_admin.action as action


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


class WorkspaceLogger(action.Action):
    def __init__(self, http, mtm_base_url):
        self.http = http
        self.mtm_base_url = mtm_base_url

    def perform(self):
        payload = self._parse_jwt_payload()
        workspace_id = payload['principal']['permission']['workspaceId']
        response = self.http.get(self.mtm_base_url + '/workspaces/' + workspace_id)
        response.raise_for_status()
        workspace_name = response.json()['data']['name']
        print('Logged in to workspace:', workspace_name)

    def _parse_jwt_payload(self):
        token = self.http.auth.obtain_access_token()
        logging.debug("JWT Token = %s", token)
        payload = jwt.decode(token, verify=False)
        logging.debug("Access Token = %s", payload)

        return payload
