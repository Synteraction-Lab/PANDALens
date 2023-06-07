from src.Action.Action import Action
from src.Command import CommandParser


class PhotoPendingAction(Action):
    def __init__(self, sys_config):
        super().__init__()
        self.system_config = sys_config

    def execute(self):
        auto_photo_command = CommandParser.parse("auto_photo", self.system_config)
        if auto_photo_command is not None:
            auto_photo_command.execute()
