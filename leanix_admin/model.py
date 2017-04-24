from leanix_admin import file
from leanix_admin.action import BackupAction, RestoreAction


class ModelBackupAction(BackupAction):
    def __init__(self, http, url, name):
        super().__init__(name)
        self.http = http
        self.url = url

    def do_perform(self):
        response = self.http.get(self.url)
        try:
            response.raise_for_status()
        except:
            print(response.json())
            raise
        model_data = response.json()['data']
        file.write_to_disk(self.name, model_data)


class ModelRestoreAction(RestoreAction):
    def __init__(self, http, url, name, force):
        super().__init__(name)
        self.http = http
        self.url = url
        self.force = force

    def do_perform(self):
        data_model = file.read_from_disk(self.name)
        url = self.url
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
