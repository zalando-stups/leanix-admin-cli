import base64
import json

import click
import os
import requests

import leanix_admin.auth as auth
import leanix_admin.graphql as graphql
import leanix_admin.model as model


def find_by_name(needle, haystack):
    for current in haystack:
        if needle['name'] == current['name']:
            return current
    return None


models = {
    'data-model': '/models/dataModel',
    'view-model': '/models/viewModel',
    'auth-model': '/models/authorization',
    'lang-en-model': '/models/languages/en'
}


class LeanixAdmin:

    def __init__(self, api_token, mtm_base_url, admin_base_url, force=False):
        self.mtm_base_url = mtm_base_url
        self.admin_base_url = admin_base_url
        self.force = force
        self.auth = auth.LeanixAuth(api_token, mtm_base_url + '/oauth2/token')
        self.http = requests.session()
        self.http.auth = self.auth

        self.restore_actions = []
        for name, api_path in models.items():
            self.restore_actions.append(model.ModelRestoreAction(self.http, admin_base_url + api_path, name, force))

        self.backup_actions = []
        for name, api_path in models.items():
            self.backup_actions.append(model.ModelBackupAction(self.http, admin_base_url + api_path, name))


    def restore(self):
        self._print_workspace()
        for action in self.restore_actions:
            action.perform()
        if click.confirm('Continue restoring backups?', default=True):
            self._restore_tag_groups()

    def backup(self):
        self._print_workspace()
        for action in self.backup_actions:
            action.perform()
        if click.confirm('Continue downloading backups?', default=True):
            self._backup_tag_groups()

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

    def _restore_tag_groups(self):
        print('Restoring tag groups...')
        current_tag_groups = self._fetch_tag_groups(erase_id=False)
        desired_tag_groups = self._read_from_disk('tag-groups')

        for desired_tag_group in desired_tag_groups:
            current_tag_group = find_by_name(desired_tag_group, current_tag_groups)
            if current_tag_group:
                desired_tag_group['id'] = current_tag_group['id']
                self._update_tag_group(desired_tag_group)
                current_tags = current_tag_group.get('tags', [])
            else:
                self._create_tag_group(desired_tag_group)
                current_tags = []
            self._restore_tags(desired_tag_group['id'], desired_tag_group.get('tags', []), current_tags)

        for current_tag_group in current_tag_groups:
            if not find_by_name(current_tag_group, desired_tag_groups):
                for tag in current_tag_group.get('tags', []):
                    self._delete_tag(tag)
                self._delete_tag_group(current_tag_group)

    def _create_tag_group(self, tag_group):
        body = {'operationName': None,
                'query': graphql.create_tag_group,
                'variables': tag_group}
        r = self.http.post(self.admin_base_url + '/graphql', json=body)
        r.raise_for_status()
        r_body = r.json()
        errors = r_body['errors']
        if errors:
            print(errors)
            print('Request: ', body)
            raise Exception()
        tag_group['id'] = r_body['data']['createTagGroup']['id']

    def _update_tag_group(self, tag_group):
        def tag_group_patches(tg):
            short_name = tg['shortName']
            description = tg['description']
            return [
                {'op': 'replace', 'path': '/mode', 'value': tg['mode']},
                {'op': 'replace', 'path': '/restrictToFactSheetTypes',
                 'value': json.dumps(tg['restrictToFactSheetTypes'])},
                ({'op': 'replace', 'path': '/shortName', 'value': short_name} if short_name else {'op': 'remove', 'path': '/shortName'}),
                ({'op': 'replace', 'path': '/description', 'value': description} if description else {'op': 'remove', 'path': '/description'})
            ]

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
            print('Request: ', body)
            raise Exception()

    def _delete_tag_group(self, tag_group):
        body = {'operationName': None,
                'query': graphql.delete_tag_group,
                'variables': {'id': tag_group['id']}}
        r = self.http.post(self.admin_base_url + '/graphql', json=body)
        r.raise_for_status()
        r_body = r.json()
        errors = r_body['errors']
        if errors:
            print(errors)
            print('Request: ', body)
            raise Exception()

    def _restore_tags(self, tag_group_id, desired_tags, current_tags):
        for desired_tag in desired_tags:
            current_tag = find_by_name(desired_tag, current_tags)
            if current_tag:
                desired_tag['id'] = current_tag['id']
                self._update_tag(desired_tag)
            else:
                desired_tag['tagGroupId'] = tag_group_id
                self._create_tag(desired_tag)

        for current_tag in current_tags:
            if not find_by_name(current_tag, desired_tags):
                self._delete_tag(current_tag)

    def _create_tag(self, tag):
        body = {'operationName': None,
                'query': graphql.create_tag,
                'variables': tag}
        r = self.http.post(self.admin_base_url + '/graphql', json=body)
        r.raise_for_status()
        r_body = r.json()
        errors = r_body['errors']
        if errors:
            print(errors)
            print('Request: ', body)
            raise Exception()
        tag['id'] = r_body['data']['createTag']['id']

    def _update_tag(self, tag):
        def tag_patches(t):
            description = t['description']
            return [
                ({'op': 'replace', 'path': '/description', 'value': description} if description else {'op': 'remove',
                                                                                                      'path': '/description'}),
                {'op': 'replace', 'path': '/color', 'value': t['color']},
                {'op': 'replace', 'path': '/status', 'value': t['status']}
            ]

        body = {'operationName': None,
                'query': graphql.update_tag,
                'variables': {'id': tag['id'],
                              'patches': tag_patches(tag)}}
        r = self.http.post(self.admin_base_url + '/graphql', json=body)
        r.raise_for_status()
        r_body = r.json()
        errors = r_body['errors']
        if errors:
            print(errors)
            print('Request: ', body)
            raise Exception()

    def _delete_tag(self, tag):
        body = {'operationName': None,
                'query': graphql.delete_tag,
                'variables': {'id': tag['id']}}
        r = self.http.post(self.admin_base_url + '/graphql', json=body)
        r.raise_for_status()
        r_body = r.json()
        errors = r_body['errors']
        if errors:
            print(errors)
            print('Request: ', body)
            raise Exception()

    def _backup_tag_groups(self):
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

    @staticmethod
    def _read_from_disk(name):
        file_name = './' + name + '.json'
        with open(file_name, 'r') as f:
            return json.load(f)

    @staticmethod
    def _write_to_disk(name, data):
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
