from src.Command.AskUserCommentOnPhotoCommand import AskUserCommentOnPhotoCommand
from src.Command.AutoPhotoCommand import AutoPhotoCommand
from src.Command.GetImageInfoCommand import GetImageInfoCommand
from src.Command.NewRecordingCommand import NewRecordingCommand
from src.Command.PhotoCommand import PhotoCommand
from src.Command.SentGPTRequestCommand import SendGPTRequestCommand
from src.Command.ShowAudioFeedbackCommand import ShowAudioFeedbackCommand
from src.Command.ShowTextFeedbackCommand import ShowTextFeedbackCommand
from src.Command.SummarizingCommand import SummarizingCommand
from src.Command.TranscribeVoiceCommand import TranscribeVoiceCommand


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
    elif command_string == "auto_photo":
        return AutoPhotoCommand(sys_config)
    elif command_string == "ask_user_comment_on_photo":
        return AskUserCommentOnPhotoCommand(sys_config)
    elif command_string == "transcribe_voice":
        return TranscribeVoiceCommand(sys_config)
    elif command_string == "get_image_info":
        return GetImageInfoCommand(sys_config)
    elif command_string == "send_gpt_request":
        return SendGPTRequestCommand(sys_config)
    elif command_string == "show_text_feedback":
        return ShowTextFeedbackCommand(sys_config)
    elif command_string == "show_audio_feedback":
        return ShowAudioFeedbackCommand(sys_config)
    else:
        return None



