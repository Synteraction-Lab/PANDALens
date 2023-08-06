import time

from src.Action.Action import Action
from src.Command import CommandParser


class AudioCommentsPendingAction(Action):
    def __init__(self, sys_config):
        super().__init__()
        self.system_config = sys_config

    def execute(self):
        self.system_config.notification = {'notif_type': 'audio_icon',
                                           'label': self.system_config.interesting_audio,
                                           'position': 'middle-right'}
        time.sleep(5)
        # self.system_config.audio_feedback_to_show = self.system_config.notification
