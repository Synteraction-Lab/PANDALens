from src.Command.Command import Command


class AskUserCommentOnPhotoCommand(Command):
    def __init__(self, sys_config):
        super().__init__()
        self.system_config = sys_config

    def execute(self):
        notification = f"We find you seem to interested in your front scene. Any comments?"
        print(notification)
