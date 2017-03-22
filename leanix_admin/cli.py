import base64
import json
import os

import click
import requests
import requests.auth


def obtain_access_token(api_token, mtm_base_url):
    response = requests.post(mtm_base_url + '/oauth2/token',
                             data={'grant_type': 'client_credentials'},
                             auth=('apitoken', api_token))
    response.raise_for_status()
    return response.json()['access_token']


class LeanixAuth(requests.auth.AuthBase):
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


class LeanixAdmin:
    models = {
        'data-model': '/models/dataModel',
        'view-model': '/models/viewModel',
        'auth-model': '/models/authorization',
        'lang-en-model': '/models/languages/en'
    }

    def __init__(self, api_token, mtm_base_url, admin_base_url):
        self.mtm_base_url = mtm_base_url
        self.admin_base_url = admin_base_url
        self.auth = LeanixAuth(api_token, mtm_base_url + '/oauth2/token')
        self.http = requests.session()
        self.http.auth = self.auth

    def backup(self):
        self._print_workspace()
        if click.confirm('Continue downloading backups?', default=True):
            for name, api_path in self.models.items():
                print('Backing up {}...'.format(name))
                self._download_model(name, api_path)

    def restore(self, force):
        self._print_workspace()
        if click.confirm('Continue restoring backups?', default=True):
            for name, api_path in self.models.items():
                print('Restoring {}...'.format(name))
                self._upload_model(name, api_path, force)

    def _print_workspace(self):
        jwt = self.auth.obtain_access_token()
        payload_part = jwt.split('.')[1]
        payload = json.loads(base64.b64decode(payload_part))
        workspace_id = payload['principal']['permission']['workspaceId']
        response = self.http.get(self.mtm_base_url + '/workspaces/' + workspace_id)
        response.raise_for_status()
        workspace_name = response.json()['data']['name']
        print('Logged in to workspace:', workspace_name)

    def _upload_model(self, name, api_path, force):
        file_name = './' + name + '.json'
        with open(file_name, 'r') as f:
            data_model = json.load(f)
        url = self.admin_base_url + api_path
        if force:
            url += "?force=true"
        response = self.http.put(url, json=data_model)
        try:
            response.raise_for_status()
        except:
            try:
                print(response.json())
            except:
                pass
            raise

    def _download_model(self, name, api_path):
        response = self.http.get(self.admin_base_url + api_path)
        try:
            response.raise_for_status()
        except:
            print(response.json())
            raise
        model_data = response.json()['data']

        file_name = './' + name + '.json'
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        with open(file_name, 'w') as f:
            json.dump(model_data, f, indent=4)


api_token_option = click.option('--api-token', envvar='LX_API_TOKEN', prompt=True, hide_input=True,
                                help='A valid LeanIX API token. '
                                     'See http://dev.leanix.net/v4.0/docs/authentication#section-generate-api-tokens')
mtm_base_url_option = click.option('--mtm-base-url', envvar='LX_MTM_BASE_URL',
                                   default='https://demo.leanix.net/services/mtm/v1')
admin_base_url_option = click.option('--admin-base-url', envvar='LX_ADMIN_BASE_URL',
                                     default='https://demo.leanix.net/beta/api/v1')

@click.group()
def cli():
    pass


@cli.command()
@api_token_option
@mtm_base_url_option
@admin_base_url_option
def backup(api_token, mtm_base_url, admin_base_url):
    admin = LeanixAdmin(api_token=api_token,
                        mtm_base_url=mtm_base_url,
                        admin_base_url=admin_base_url)
    admin.backup()


@cli.command()
@api_token_option
@mtm_base_url_option
@admin_base_url_option
@click.option('--force/--no-force', default=False)
def restore(api_token, mtm_base_url, admin_base_url, force):
    admin = LeanixAdmin(api_token=api_token,
                        mtm_base_url=mtm_base_url,
                        admin_base_url=admin_base_url)
    admin.restore(force)


def main():
    cli()
