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
- An OpenAI account to access the GPT API.


## Installation and Setup

1. Clone the repository to your local machine.
2. Run `pip install -r requirements.txt` to install the necessary Python packages.
3. Set your environment variables with your OpenAI API keys. You will need two keys in our case (create them here: [OpneAI Account](https://platform.openai.com/account/api-keys)), which can be set as follows:

   - Windows: 

      - Option 1: Set your ‘OPENAI_API_KEY’ Environment Variable via the cmd prompt:

         Run the following in the cmd prompt, replacing `<yourkey>` with your API key:
      
         ```setx OPENAI_API_KEY_U1 "<yourkey1>"```
     
         ```setx OPENAI_API_KEY_U2 "<yourkey2>"```

         This will apply to future cmd prompt windows, so you will need to open a new one to use that variable with Python. You can validate that this variable has been set by opening a new cmd prompt window and typing in 

         ```echo %OPENAI_API_KEY_U1%```
     
         ```echo %OPENAI_API_KEY_U2%```

      - Option 2: Set your ‘OPENAI_API_KEY’ Environment Variable through the Control Panel:

         1. Open System properties and select Advanced system settings.
         2. Select Environment Variables.
         3. Select New from the User variables section (top). Add your name/key value pair, replacing `<yourkey>` with your API key.

            Variable name: `OPENAI_API_KEY_U1`, Variable value: `<yourkey1>`

            Variable name: `OPENAI_API_KEY_U2`, Variable value: `<yourkey2>`

   - Linux / MacOS:

      - Option 1: Set your ‘OPENAI_API_KEY’ Environment Variable using zsh:

         1. Run the following command in your terminal, replacing `<yourkey>` with your API key.

            ```echo "export OPENAI_API_KEY_U1='yourkey1'" >> ~/.zshrc```
            ```echo "export OPENAI_API_KEY_U2='yourkey2'" >> ~/.zshrc```

         2. Update the shell with the new variable:

            ```source ~/.zshrc```

         3. Confirm that you have set your environment variable using the following command.

            ```echo $OPENAI_API_KEY_U1```
            ```echo $OPENAI_API_KEY_U2```

        - Option 2: Set your ‘OPENAI_API_KEY’ Environment Variable using bash:
          Follow the directions in Option 1, replacing `.zshrc` with `.bash_profile`.
4. If you want to support more writing tasks, please create the task description from [OpenAI](https://platform.openai.com/playground/p/default-chat?model=text-davinci-003) first then create {YOUR_TASK_TYPE}.txt file in ``data/task_description`` folder. 
You can also modify the prompt in this folder to improve the experience.

## Windows specific issues
- Windows defender issue
  - Windows defender will treat the keyboardListener in App.py as a threat and automatically delete the file 
    - To overcome this problem, follow these steps
      1. Press Windows + I keys and open Settings
      2. Click on Update & Security
      3. Go to Windows Security
      4. Click on Virus & Threat protection
      5. Select Manage Settings
      6. Under Exclusions, click on Add or remove exclusion
      7. Click on the + sign which says Add an exclusion
      8. Select File, Folder, File Type or Process

## MacOS specific issues
- pyttsx3 issue
  - If you meet the issue with `AttributeError: 'super' object has no attribute 'init'` when using the pyttsx3 on macOS
    - Please follow the [instruction](https://github.com/RapidWareTech/pyttsx/pull/35/files) to add `from objc import super` at the top of the `/path_to_your_venv/pyttsx3/drivers/nsss.py` file.

## Manipulation For Travel Blog

### Step 1
- Run ``python main.py``

### Step 2
- Set up your device & task, including entering the user_id, selecting task type and output modality, and selecting your source for voice recording.
- Click "Save" to save the configuration.

### Step 3
- You can use our ring mouse to manipulate the menu. You can use your mouse and keyboard if you use it for desktop setting.
  - To start a new recording, press ``arrow_right`` key on your keyboard or click the right button in the GUI. 
  - To get a summarization or generate full writing, press ``arrow_up`` key on your keyboard or click the top button in the GUI. 
  - To take a picture, please press ``arrow_down`` key on your keyboard or click the bottom button in the GUI. If you want to make any comments on the picture, after the picture windows shows up, you can start a new recording and say your comments following the above instructions.
  - To hide/show the picture window or text, please press ``arrow_left`` key on your keyboard or click the left button in the GUI.
  - You can scroll your mouse wheel to scroll up and down the generated writing.

### Step 4
If you want to check your full conversation history with GPT, you can check the history recording in the ``data/recording/{USER_ID}/chat_history.json`` folder.

### Step 5 (OPTIONAL: DEBUGGING MODE)

If you want to rerun the program and load the previous chat history (with the same PID), you can press the `Esc` key on the keyboard. 

However, please note that we cannot guarantee that it will resume your entire chat history, as OpenAI has limitations on the length of requests.

## References

- https://realpython.com/python-virtual-environments-a-primer/
- https://phoenixnap.com/kb/ffmpeg-windows
- https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety



