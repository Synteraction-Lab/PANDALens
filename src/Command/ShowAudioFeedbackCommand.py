from src.Command.Command import Command


class ShowAudioFeedbackCommand(Command):
    def __init__(self, sys_config):
        super().__init__()
        self.system_config = sys_config

    def execute(self):
        print(f"\nAudio Feedback:\n{self.system_config.audio_feedback_to_show}")
