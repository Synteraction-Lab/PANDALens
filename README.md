# PANDALens
A software that enables you to write ubiquitously on OHMD with the assistance of GPT.

## Publications
- [PANDALens: Towards AI-Assisted In-Context Writing on OHMD During Travels](https://doi.org/10.1145/3613904.3642320), CHI'2024
  - Full Paper Camera Ready [PDF]: [PANDALens: Towards AI-Assisted In-Context Writing on OHMD During Travels](https://dl.acm.org/doi/pdf/10.1145/3613904.3642320).
  - ```
    Runze Cai, Nuwan Janaka, Yang Chen, Lucia Wang, Shengdong Zhao,
    and Can Liu. 2024. PANDALens: Towards AI-Assisted In-Context Writing
    on OHMD During Travels. In Proceedings of the CHI Conference on Human
    Factors in Computing Systems (CHI ’24), May 11–16, 2024, Honolulu, HI, USA.
    ACM, New York, NY, USA, 24 pages. https://doi.org/10.1145/3613904.3642320
    
    ```
  - CHI Interactivity 2024 (Demo Paper): [Demonstrating PANDALens: Enhancing Daily Activity Documentation with AI-assisted In-Context Writing on OHMD](https://doi.org/10.1145/3613905.3648644), Camera Ready [PDF](paper/Demonstrating_PANDALens_CHIEA24.pdf) [POSTER](paper/PANDALens_poster.pdf).

 


## Contact person
- [Runze Cai](http://runzecai.com)


## Requirements
- Python 3.9.18 (better to create a new [conda env](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) or [virtual environment](https://realpython.com/python-virtual-environments-a-primer/) first.)
- **Note: macOS is the preferred and verified OS, as many functions (e.g., GPS and text-to-speech) in the release code use the macOS native APIs.** But feel free to replace them with other APIs when you are using another OS.
- Install [FFmpeg](https://ffmpeg.org/) and add it to your environment path.
  - For macOS, you can use [`brew install ffmpeg`](https://formulae.brew.sh/formula/ffmpeg).
  - For Windows, you may need to [manually add it to the environment variable](https://phoenixnap.com/kb/ffmpeg-windows).
- An OpenAI account to access the GPT API, a Hugging Face account to access the BLIP API, and a Google Cloud Account to access the Vision API.
- [Pupil Lab software](https://docs.pupil-labs.com/core/) for eye tracking.


## Installation and Setup

1. Clone the repository to your local machine.
2. Run `pip install -r requirements.txt` to install the necessary Python packages.
3. Set your environment variables with your OpenAI API keys (Note: OPENAI_API_KEY_U1 and OPENAI_API_KEY_U2 can be identical. Different keys are set to prevent invalid requests due to request limitation for one key). You will need two keys in our case (create them here: [OpneAI Account](https://platform.openai.com/account/api-keys)), which can be set as follows:

   - MacOS:

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
   -  Windows: 

      - Option 1: Set your ‘OPENAI_API_KEY’ Environment Variable via the cmd prompt:

         Run the following in the cmd prompt, replacing `<yourkey>` with your API key:
      
         ```setx OPENAI_API_KEY_U1 "<yourkey1>"```
        
     
         ```setx OPENAI_API_KEY_U2 "<yourkey2>"```

         This will apply to future cmd prompt windows, so you will need to open a new one to use that variable with Python. You can validate that this variable has been set by opening a new cmd prompt window and typing in. 

         ```echo %OPENAI_API_KEY_U1%```
        
     
         ```echo %OPENAI_API_KEY_U2%```

      - Option 2: Set your ‘OPENAI_API_KEY’ Environment Variable through the Control Panel:

         1. Open System properties and select Advanced system settings.
         2. Select Environment Variables.
         3. Select New from the User variables section (top). Add your name/key-value pair, replacing `<yourkey>` with your API key.

            Variable name: `OPENAI_API_KEY_U1`, Variable value: `<yourkey1>`

            Variable name: `OPENAI_API_KEY_U2`, Variable value: `<yourkey2>`
4. (Ignore this step for new version by default if you use the GPT-4o to describe image) Follow the same approach above; add `HUGGINGFACE_API_KEY` to your environment variable. See more details at [HuggingFace API](https://huggingface.co/docs/api-inference/quicktour).
5. Set up your Google Cloud Vision following these guides: [Google Cloud Vision Setup](https://cloud.google.com/vision/docs/setup)
and [Use Client Libraries](https://cloud.google.com/vision/docs/detect-labels-image-client-libraries)
6. If you want to support more writing tasks, please create the task description from [OpenAI](https://platform.openai.com/playground/p/default-chat?model=text-davinci-003) first, then create {YOUR_TASK_TYPE}.txt file in ``data/task_description`` folder. 
You can also modify the prompt in this folder to improve the experience.

## Windows-specific issues
- Windows defender issue
  - Windows Defender will treat the keyboardListener in App.py as a threat and automatically delete the file 
    - To overcome this problem, follow these steps
      1. Press the Windows + I keys and open Settings
      2. Click on Update & Security
      3. Go to Windows Security
      4. Click on Virus & Threat protection
      5. Select Manage Settings
      6. Under Exclusions, click on Add or Remove exclusion
      7. Click on the + sign which says Add an exclusion
      8. Select File, Folder, File Type, or Process

## MacOS specific issues
- pyttsx3 issue
  - If you meet the issue with `AttributeError: 'super' object has no attribute 'init'` when using the pyttsx3 on macOS
    - Please follow the [instruction](https://github.com/RapidWareTech/pyttsx/pull/35/files) to add `from objc import super` at the top of the `/path_to_your_venv/pyttsx3/drivers/nsss.py` file.

## Issue with some Python packages
1. [Fix the code of the image quality analysis](https://github.com/ocampor/image-quality/pull/51).

## Manipulation For Travel Blog

### Step 1
- Run ``sudo -S "/Applications/Pupil Capture.app/Contents/MacOS/pupil_capture"`` in your terminal to start the Pupil Lab software for macOS.

### Step 2
- Run ``python main.py``

### Step 3
- Set up your device & task, including entering the user_id, selecting task type and output modality, and selecting your source for voice recording.
- Click "Save" to save the configuration.

### Step 4
- You can use our ring mouse to manipulate the menu. You can use your mouse and keyboard if you use it for desktop settings.
  - To start a new recording, press the ``arrow_right`` key on your keyboard or click the right button in the GUI. 
  - To get a summarization or generate full writing, press the ``arrow_up`` key on your keyboard or click the top button in the GUI. 
  - To take a picture, please press the ``arrow_down`` key on your keyboard or click the bottom button in the GUI. If you want to make any comments on the picture, after the picture windows show up, you can start a new recording and say your comments following the above instructions.
  - To hide/show the GUI, please click the mouse's left button.
  - You can scroll your mouse wheel up and down the generated writing.
  - To map the ring interaction to the above settings, you can leverage tools, e.g., Karabiner-Elements.

### Step 5
If you want to generate a travel blog, please press the ``right_command`` key on your keyboard then enter the title in GUI.
Then, you can find the exported file in the ``data`` folder. 

To check your full conversation history with GPT, you can check the history recording in the ``data/recording/{USER_ID}/chat_history.json`` folder.

### Step 6 (OPTIONAL: DEBUGGING MODE)

If you want to rerun the program and load the previous chat history (with the same PID), press the `Esc` key on the keyboard. 

However, please keep in mind that we cannot promise that it will resume your entire chat history, as OpenAI has limitations on the length of requests.

### Step 8 (OPTIONAL: REPLACE AUDIO FEEDBACK SOUND)

In the released code, we leverage the free and native text-to-speech API in macOS. If you use another OS or want a better user experience, we recommend replacing the API with Google's or OpenAI's text-to-speech API.

## References

- https://realpython.com/python-virtual-environments-a-primer/
- https://phoenixnap.com/kb/ffmpeg-windows
- https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety



