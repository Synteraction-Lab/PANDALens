from src.Action.CommentsOnGPTResponseAction import CommentsOnGPTResponseAction
from src.Action.CommentsOnPhotoAction import CommentsOnPhotoAction
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
    elif command_string == "comments_on_photo":
        return CommentsOnPhotoAction(sys_config)
    elif command_string == "show_gpt_response":
        return ShowGPTResponseAction(sys_config)
    elif command_string == "comments_on_gpt_response":
        return CommentsOnGPTResponseAction(sys_config)
    else:
        return None
