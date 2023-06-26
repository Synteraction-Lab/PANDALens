from src.Action.Action import Action
from src.Command import CommandParser


class ManualPhotoCommentsPendingAction(Action):
    def __init__(self, sys_config):
        super().__init__()
        self.system_config = sys_config

    def execute(self):
        manual_photo_command = CommandParser.parse("manual_photo", self.system_config)
        if manual_photo_command is not None:
            manual_photo_command.execute()


            