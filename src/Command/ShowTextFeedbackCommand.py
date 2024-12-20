from src.Command.Command import Command


class ShowTextFeedbackCommand(Command):
    def __init__(self, sys_config):
        super().__init__()
        self.system_config = sys_config

    def execute(self):
        print(f"\nText feedback:\n{self.system_config.text_feedback_to_show}")
