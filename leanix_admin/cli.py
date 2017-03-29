import base64
import json

import click
import os
import requests
import requests.auth as requests_auth

import leanix_admin.graphql as graphql


def obtain_access_token(api_token, mtm_base_url):
    response = requests.post(mtm_base_url + '/oauth2/token',
                             data={'grant_type': 'client_credentials'},
                             auth=('apitoken', api_token))
    response.raise_for_status()
    return response.json()['access_token']


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


class LeanixAdmin:
    models = {
        'data-model': '/models/dataModel',
        'view-model': '/models/viewModel',
        'auth-model': '/models/authorization',
        'lang-en-model': '/models/languages/en'
    }

    def __init__(self, api_token, mtm_base_url, admin_base_url, force=False):
        self.mtm_base_url = mtm_base_url
        self.admin_base_url = admin_base_url
        self.force = force
        self.auth = LeanixAuth(api_token, mtm_base_url + '/oauth2/token')
        self.http = requests.session()
        self.http.auth = self.auth

    def restore(self):
        self._print_workspace()
        if click.confirm('Continue restoring backups?', default=True):
            self._restore_models()
            self._restore_tags()

    def backup(self):
        self._print_workspace()
        if click.confirm('Continue downloading backups?', default=True):
            self._backup_models()
            self._backup_tags()

    def _print_workspace(self):
        jwt = self.auth.obtain_access_token()
        payload_part = jwt.split('.')[1]
        # fix missing padding for this base64 encoded string.
        # If number of bytes is not dividable by 4, append '=' until it is.
        missing_padding = len(payload_part) % 4
        if missing_padding != 0:
            payload_part += '='* (4 - missing_padding)
        payload = json.loads(base64.b64decode(payload_part))
        workspace_id = payload['principal']['permission']['workspaceId']
        response = self.http.get(self.mtm_base_url + '/workspaces/' + workspace_id)
        response.raise_for_status()
        workspace_name = response.json()['data']['name']
        print('Logged in to workspace:', workspace_name)

    def _restore_models(self):
        for name, api_path in self.models.items():
            print('Restoring {}...'.format(name))
            self._upload_model(name, api_path)

    def _upload_model(self, name, api_path):
        data_model = self._read_from_disk(name)
        url = self.admin_base_url + api_path
        if self.force:
            url += "?force=true"
        response = self.http.put(url, json=data_model)
        try:
            response.raise_for_status()
        except:
            try:
                print(response.json())
            except ValueError:
                pass
            raise

    def _restore_tags(self):
        print('Restoring tag groups...')
        current_tag_groups = self._fetch_tag_groups(erase_id=False)
        desired_tag_groups = self._read_from_disk('tag-groups')

        def find_tag_group_in(needle, haystack):
            for tag_group in haystack:
                if needle['name'] == tag_group['name']:
                    return tag_group
            return None

        to_be_created = []
        to_be_updated = []
        to_be_deleted = []

        for desired_tag_group in desired_tag_groups:
            current_tag_group = find_tag_group_in(desired_tag_group, current_tag_groups)
            if current_tag_group:
                desired_tag_group['id'] = current_tag_group['id']
                to_be_updated.append(desired_tag_group)
            else:
                to_be_created.append(desired_tag_group)

        for current_tag_group in current_tag_groups:
            if not find_tag_group_in(current_tag_group, desired_tag_groups):
                to_be_deleted.append(current_tag_group)

        for tag_group in to_be_created:
            body = {'operationName': None,
                    'query': graphql.create_tag_group,
                    'variables': tag_group}
            r = self.http.post(self.admin_base_url + '/graphql', json=body)
            r.raise_for_status()
            r_body = r.json()
            errors = r_body['errors']
            if errors:
                print(errors)
                raise Exception()
            tag_group['id'] = r_body['data']['createTagGroup']['id']

        def tag_group_patches(tag_group):
            return [
                {'op': 'replace', 'path': '/mode', 'value': tag_group['mode']},
                {'op': 'replace', 'path': '/restrictToFactSheetTypes',
                 'value': json.dumps(tag_group['restrictToFactSheetTypes'])},
                {'op': 'replace', 'path': '/shortName', 'value': tag_group['shortName']},
                {'op': 'replace', 'path': '/description', 'value': tag_group['description']}
            ]

        for tag_group in to_be_updated:
            body = {'operationName': None,
                    'query': graphql.update_tag_group,
                    'variables': {'id': tag_group['id'],
                                  'patches': tag_group_patches(tag_group)}}
            r = self.http.post(self.admin_base_url + '/graphql', json=body)
            r.raise_for_status()
            r_body = r.json()
            errors = r_body['errors']
            if errors:
                print(errors)
                raise Exception()

        for tag_group in to_be_deleted:
            body = {'operationName': None,
                    'query': graphql.delete_tag_group,
                    'variables': {'id': tag_group['id']}}
            r = self.http.post(self.admin_base_url + '/graphql', json=body)
            r.raise_for_status()
            r_body = r.json()
            errors = r_body['errors']
            if errors:
                print(errors)
                raise Exception()

    def _backup_models(self):
        for name, api_path in self.models.items():
            print('Backing up {}...'.format(name))
            self._download_model(name, api_path)

    def _download_model(self, name, api_path):
        response = self.http.get(self.admin_base_url + api_path)
        try:
            response.raise_for_status()
        except:
            print(response.json())
            raise
        model_data = response.json()['data']
        self._write_to_disk(name, model_data)

    def _backup_tags(self):
        print('Backing up tag groups...')
        tag_groups = self._fetch_tag_groups()
        self._write_to_disk('tag-groups', tag_groups)

    def _fetch_tag_groups(self, erase_id=True):
        body = {'operationName': None,
                'query': graphql.list_tag_groups,
                'variables': {}}
        r = self.http.post(self.admin_base_url + '/graphql', json=body)
        r.raise_for_status()
        r_body = r.json()
        errors = r_body['errors']
        if errors:
            print(errors)
            raise Exception()
        tag_groups = []
        for tag_group_edge in r_body.get('data', {}).get('listTagGroups', {}).get('edges', []):
            tag_group = tag_group_edge['node']
            tags = []
            for tag_edge in tag_group.get('tags', {}).get('edges', []):
                tag = tag_edge['node']
                if erase_id:
                    del tag['id']
                tags.append(tag)

            tag_group['tags'] = tags
            if erase_id:
                del tag_group['id']
            tag_groups.append(tag_group)
        return tag_groups

    def _read_from_disk(self, name):
        file_name = './' + name + '.json'
        with open(file_name, 'r') as f:
            return json.load(f)

    def _write_to_disk(self, name, data):
        file_name = './' + name + '.json'
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        with open(file_name, 'w') as f:
            json.dump(data, f, indent=4)


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
                        admin_base_url=admin_base_url,
                        force=force)
    admin.restore()


def main():
    cli()
