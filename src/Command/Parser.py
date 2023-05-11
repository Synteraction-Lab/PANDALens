from src.Command.NewRecordingCommand import NewRecordingCommand
from src.Command.PhotoCommand import PhotoCommand
from src.Command.SummarizingCommand import SummarizingCommand


# parser the input and return a command
def parse(command_string, sys_config):
    # List of commands that can be parsed:
    """
    "new": new recording
    "summary": summarize the recording
    "photo": take a photo
    """
    if command_string == "new":
        return NewRecordingCommand(sys_config)
    elif command_string == "summary":
        return SummarizingCommand(sys_config)
    elif command_string == "photo":
        return PhotoCommand(sys_config)
    else:
        return None



