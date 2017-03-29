import click


class Action:
    def perform(self):
        pass


class ConfirmableAction:
    def __init__(self, action, name):
        super().__init__()
        self.action = action
        self.name = name

    def perform(self):
        if click.confirm('{} {}?'.format(self.action, self.name), default=True):
            self.do_perform()
            print('done.')
        else:
            print('skipped.')

    def do_perform(self):
        pass


class BackupAction(ConfirmableAction):
    def __init__(self, name):
        super().__init__('Backup', name)


class RestoreAction(ConfirmableAction):
    def __init__(self, name):
        super().__init__('Restore', name)
