import json

import leanix_admin.file as file
import leanix_admin.graphql as graphql
from leanix_admin.action import BackupAction, RestoreAction


def find_by_name(needle, haystack):
    for current in haystack:
        if needle['name'] == current['name']:
            return current
    return None


class TagGroupsBase:
    def __init__(self, http, graphql_url):
        self.http = http
        self.graphql_url = graphql_url

    def _fetch_tag_groups(self, erase_id=True):
        body = {'operationName': None,
                'query': graphql.list_tag_groups,
                'variables': {}}
        r = self.http.post(self.graphql_url, json=body)
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


class TagGroupsBackupAction(TagGroupsBase, BackupAction):
    def __init__(self, http, graphql_url):
        TagGroupsBase.__init__(self, http, graphql_url)
        BackupAction.__init__(self, name='tag-groups')
        self.http = http
        self.graphql_url = graphql_url

    def do_perform(self):
        tag_groups = self._fetch_tag_groups()
        file.write_to_disk(self.name, tag_groups)


class TagGroupsRestoreAction(TagGroupsBase, RestoreAction):
    def __init__(self, http, graphql_url):
        TagGroupsBase.__init__(self, http, graphql_url)
        RestoreAction.__init__(self, name='tag-groups')
        self.http = http
        self.graphql_url = graphql_url

    def do_perform(self):
        current_tag_groups = self._fetch_tag_groups(erase_id=False)
        desired_tag_groups = file.read_from_disk(self.name)

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
        r = self.http.post(self.graphql_url, json=body)
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
                ({'op': 'replace', 'path': '/shortName', 'value': short_name} if short_name else {'op': 'remove',
                                                                                                  'path': '/shortName'}),
                ({'op': 'replace', 'path': '/description', 'value': description} if description else {'op': 'remove',
                                                                                                      'path': '/description'})
            ]

        body = {'operationName': None,
                'query': graphql.update_tag_group,
                'variables': {'id': tag_group['id'],
                              'patches': tag_group_patches(tag_group)}}
        r = self.http.post(self.graphql_url, json=body)
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
        r = self.http.post(self.graphql_url, json=body)
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
        r = self.http.post(self.graphql_url, json=body)
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
        r = self.http.post(self.graphql_url, json=body)
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
        r = self.http.post(self.graphql_url, json=body)
        r.raise_for_status()
        r_body = r.json()
        errors = r_body['errors']
        if errors:
            print(errors)
            print('Request: ', body)
            raise Exception()
