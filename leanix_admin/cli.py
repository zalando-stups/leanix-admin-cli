import click
import requests

import leanix_admin.auth as auth
import leanix_admin.model as model
import leanix_admin.tag_group as tag_group

models = {
    'data-model': '/models/dataModel',
    'view-model': '/models/viewModel',
    'auth-model': '/models/authorization',
    'lang-en-model': '/models/languages/en'
}


class LeanixAdmin:
    def __init__(self, api_token, mtm_base_url, admin_base_url, force=False):
        http = requests.session()
        http.auth = auth.LeanixAuth(api_token, mtm_base_url + '/oauth2/token')
        graphql_url = admin_base_url + '/graphql'
        workspace_logger = auth.WorkspaceLogger(http, mtm_base_url)

        self.restore_actions = []
        self.restore_actions.append(workspace_logger)
        for name, api_path in models.items():
            self.restore_actions.append(model.ModelRestoreAction(http, admin_base_url + api_path, name, force))
        self.restore_actions.append(tag_group.TagGroupsRestoreAction(http, graphql_url))

        self.backup_actions = []
        self.backup_actions.append(workspace_logger)
        for name, api_path in models.items():
            self.backup_actions.append(model.ModelBackupAction(http, admin_base_url + api_path, name))
        self.backup_actions.append(tag_group.TagGroupsBackupAction(http, graphql_url))

    def restore(self):
        for action in self.restore_actions:
            action.perform()

    def backup(self):
        for action in self.backup_actions:
            action.perform()


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
