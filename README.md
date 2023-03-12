# UbiWriter
A software that enables you to write ubiquitously with the assistant of GPT.

## Publications
- [publication_name](publication_link), VENUE'XX
```
<Bibtext>

```

## Contact person
- [Runze Cai](http://runzecai.com)


## Project links
- Project folder: [here](project_link)
- Documentation: [here](guide_link)
- [Version info](VERSION.md)


## Requirements
- Python 3.9 (better to create a new [virtual environment](https://realpython.com/python-virtual-environments-a-primer/) first.)
- Install [FFmpeg](https://ffmpeg.org/) and add it to your environment path.
  - For macOS, you can use [`brew install ffmpeg`](https://formulae.brew.sh/formula/ffmpeg)
  - For Windows, you may need to [manually add it to the environment variable](https://phoenixnap.com/kb/ffmpeg-windows).


## Installation
- Run ``pip install -r requirements.txt``
- If you want to support more writing tasks, please create the task description from [OpenAI](https://platform.openai.com/playground/p/default-chat?model=text-davinci-003) first then create {YOUR_TASK_TYPE}.txt file in ``data/task_description`` folder. 
You can also modify the prompt in this folder to improve the experience.

## Manipulation

### Step 1
- Run ``python App.py``

### Step 2
- Set up your device & task, including entering the user_id, selecting task type and output modality, and selecting your source for voice recording.
- Click "Save" to save the configuration.

### Step 3
- You can use our ring mouse to manipulate the menu. You can use your mouse and keyboard if you use it for desktop setting.
  - To start a new recording, press ``arrow_right`` key on your keyboard. 
  - To get a summarization or generate full writing, press ``arrow_up`` key on your keyboard. 
  - To increase/decrease the window's size, please press ``arrow_down`` key on your keyboard.
  - To hide/show the content, please press ``arrow_left`` key on your keyboard.
  - You can now select text using your mouse (press and hold the mouse button, move to select content, and release to record the selection) and speak out your comments to it.
  - You can scroll your mouse wheel to scroll up and down the generated writing.

### Step 4
If you want to check your full conversation history with GPT, you can check the history recording in the ``data/recording/{USER_ID}/chat_history.json`` folder.

### Step 5 (OPTIONAL: DEBUGGING MODE)

If you want to rerun the program and load the previous chat history (with the same PID), you can press the `Esc` key on the keyboard. 

However, please note that we cannot guarantee that it will resume your entire chat history, as OpenAI has limitations on the length of requests.
## References

- https://realpython.com/python-virtual-environments-a-primer/
- https://phoenixnap.com/kb/ffmpeg-windows



