from src.Action.Action import Action
from src.Command import CommandParser


class ShowGPTResponseAction(Action):
    def __init__(self, sys_config):
        super().__init__()
        self.system_config = sys_config

    def execute(self, ui):
        show_text_feedback_command = CommandParser.parse("show_text_feedback", self.system_config)
        if show_text_feedback_command is not None:
            show_text_feedback_command.execute(ui)

        show_audio_feedback_command = CommandParser.parse("show_audio_feedback", self.system_config)
        if show_audio_feedback_command is not None:
            show_audio_feedback_command.execute(ui)




