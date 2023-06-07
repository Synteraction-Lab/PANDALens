from src.Action.CommentsOnPhotoAction import CommentsOnPhotoAction
from src.Action.CommentsToGPTAction import CommentsToGPTAction
from src.Action.FullWritingPendingAction import FullWritingPendingAction
from src.Action.ManualPhotoCommentsPendingAction import ManualPhotoCommentsPendingAction
from src.Action.PhotoCommentsPendingAction import PhotoCommentsPendingAction
from src.Action.PhotoPendingAction import PhotoPendingAction
from src.Action.ShowGPTResponseAction import ShowGPTResponseAction


# parser the input and return a action
def parse(command_string, sys_config):
    # List of commands that can be parsed:
    """
    "new": new recording
    "summary": summarize the recording
    "photo": take a photo
    """
    if command_string == "photo_pending":
        return PhotoPendingAction(sys_config)
    elif command_string == "photo_comments_pending":
        return PhotoCommentsPendingAction(sys_config)
    elif command_string == "manual_photo_comments_pending":
        return ManualPhotoCommentsPendingAction(sys_config)
    elif command_string == "comments_on_photo":
        return CommentsOnPhotoAction(sys_config)
    elif command_string == "show_gpt_response":
        return ShowGPTResponseAction(sys_config)
    elif command_string == "comments_to_gpt":
        return CommentsToGPTAction(sys_config)
    elif command_string == "full_writing_pending":
        return FullWritingPendingAction(sys_config)
    else:
        return None
