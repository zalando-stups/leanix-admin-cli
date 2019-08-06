import click
import logging
import requests

from leanix_admin import auth, model, tag_group

models = {
    'data-model': '/models/dataModel',
    'view-model': '/models/viewModel',
    'auth-model': '/models/authorization',
    'lang-en-model': '/models/languages/en',
    'reporting': '/models/reporting'
}


class LeanixAdmin:
    def __init__(self, api_token, mtm_base_url, api_base_url, force=False):
        http = requests.session()
        http.auth = auth.LeanixAuth(api_token, mtm_base_url + '/oauth2/token')
        graphql_url = api_base_url + '/graphql'
        workspace_logger = auth.WorkspaceLogger(http, mtm_base_url)

        self.restore_actions = []
        self.restore_actions.append(workspace_logger)
        for name, api_path in models.items():
            self.restore_actions.append(model.ModelRestoreAction(http, api_base_url + api_path, name, force))
        self.restore_actions.append(tag_group.TagGroupsRestoreAction(http, graphql_url))

        self.backup_actions = []
        self.backup_actions.append(workspace_logger)
        for name, api_path in models.items():
            self.backup_actions.append(model.ModelBackupAction(http, api_base_url + api_path, name))
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
api_base_url_option = click.option('--api-base-url', envvar='LX_API_BASE_URL',
                                     default='https://demo.leanix.net/beta/api/v1')
log_level_option = click.option('--log-level', envvar='LOG_LEVEL', default='WARNING')

@click.group()
@log_level_option
def cli(log_level):
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % log_level)
    logging.basicConfig(level=numeric_level)
    pass


@cli.command()
@api_token_option
@mtm_base_url_option
@api_base_url_option
def backup(api_token, mtm_base_url, api_base_url):
    admin = LeanixAdmin(api_token=api_token,
                        mtm_base_url=mtm_base_url,
                        api_base_url=api_base_url)
    admin.backup()


@cli.command()
@api_token_option
@mtm_base_url_option
@api_base_url_option
@click.option('--force/--no-force', default=False)
def restore(api_token, mtm_base_url, api_base_url, force):
    admin = LeanixAdmin(api_token=api_token,
                        mtm_base_url=mtm_base_url,
                        api_base_url=api_base_url,
                        force=force)
    admin.restore()


def main():
    cli()
