from src.Command.Command import Command


class AskUserCommentOnPhotoCommand(Command):
    def __init__(self, sys_config):
        super().__init__()
        self.system_config = sys_config

    def execute(self):
        return
        notification = f"We find you seem to interested in the scene. Any comments?"
        self.system_config.notification = {'type': 'text',
                                           'content': notification,
                                           'position': 'top-center'}
        self.system_config.audio_feedback_to_show = notification
