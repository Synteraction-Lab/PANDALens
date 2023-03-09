import os

CONFIG_FILE_NAME = "device_config.csv"
VISUAL_OUTPUT = "visual"
AUDIO_OUTPUT = "visual+audio"
ROLE_AI = "assistant"
ROLE_SYSTEM = "system"
ROLE_HUMAN = "user"
CONCISE_THRESHOLD = 8000
JOURNAL = "journal"
PAPER = "paper_writing"
SELF_REFLECTION = "reflection"
PAPER_REVIEW = "paper_review"
ALL_HISTORY = "all"
AI_HISTORY = "ai"
HUMAN_HISTORY = "human"
audio_file = "command.mp3"
chat_file = "chat_history.json"
slim_history_file = "slim_history.json"
NEW_ITEM_KEY = 'key.down'
REVISE_KEY = 'key.right'
SUMMARIZE_KEY = 'key.up'
task_description_path = os.path.join("data", "task_description")
config_path = os.path.join("data", CONFIG_FILE_NAME)
