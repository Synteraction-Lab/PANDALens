import os
import threading
import time
from datetime import datetime

import openai

from Storage.reader import load_task_description
from Storage.writer import append_data
from Utilities.constant import ALL_HISTORY, ROLE_SYSTEM, CONCISE_THRESHOLD, ROLE_HUMAN, ROLE_AI


def generate_gpt_response(sent_prompt, max_tokens=1000, temperature=0.3, id_idx=0):
    try:
        if id_idx == 0:
            openai.api_key = "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"
        else:
            openai.api_key = "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"
        model_engine = "gpt-3.5-turbo"
        response = openai.ChatCompletion.create(
            model=model_engine,
            messages=sent_prompt,
            max_tokens=max_tokens,
            n=1,
            stop=None,
            temperature=temperature,
        )
        print(response)
        response = response['choices'][0]['message']['content']

        return response
    except Exception as e:
        print(e)


class GPT:
    def __init__(self, chat_history_file_name, slim_history_file_name):
        self.task_description = None
        self.latest_request = ""
        self.slim_history = ""
        self.ai_history = ""
        self.human_history = ""
        self.chat_history = ""
        self.stored_text_widget_content = ""
        self.message_list = []

        self.send_history_mode = ALL_HISTORY

        self.chat_history_file_name = chat_history_file_name
        self.slim_history_file_name = slim_history_file_name

    def setup_chat_gpt(self, task_type):
        self.task_description = load_task_description(task_type)
        self.chat_history = self.task_description
        self.human_history = self.task_description
        self.ai_history = self.task_description
        initial_message = {"role": ROLE_SYSTEM, "content": self.task_description}
        self.message_list.append(initial_message)

    def store(self, role=ROLE_HUMAN, text=None, path=None):
        if path is None:
            path = self.chat_history_file_name
        data = {"time": str(datetime.now()), "role": role, "content": text.lstrip()}
        append_data(path, data)

    def resume_stored_history(self):
        if os.path.isfile(self.slim_history_file_name):
            with open(self.slim_history_file_name) as f:
                chat_history = f.read()
                print("Resuming the conversation: ", self.slim_history_file_name)
        else:
            with open(self.chat_history_file_name) as f:
                chat_history = f.read()
                print("Resuming the conversation: ", self.chat_history_file_name)
        response = self.process_prompt_and_get_gpt_response(command=chat_history,
                                                            prefix="Resume the conversation history (Don't show the timestamp in the following answers)",
                                                            is_prompt_stored=False)

    def append_chat_history(self, response):
        self.chat_history = self.chat_history + response

    def process_prompt_and_get_gpt_response(self, command, is_prompt_stored=True, role=ROLE_HUMAN, prefix=""):
        """
        Process a chat prompt, add it to the chat history, and generate a response using the OpenAI GPT-3.5 language model,
        and store the conversation history if required.

        Args:
            command (str): The chat prompt to process and generate a response for.
            is_prompt_stored (bool, optional): Whether to store the prompt to conversation history file. Defaults to True.
            role (str, optional): The role of the speaker. Defaults to ROLE_HUMAN.
            prefix (str, optional): Any prefix to add to the prompt. Defaults to "".

        Returns:
            str: The response generated by the OpenAI GPT-3.5 language model.
        """
        response = ""

        # Set up the prompt
        prompt = role + " :" + prefix + command
        new_message = {"role": role, "content": prefix + command}
        if is_prompt_stored:
            self.store(role=role, text=prompt)
            print(prompt)
        try:
            # Add the prompt to the conversation history
            self.chat_history = self.chat_history + prompt
            self.human_history = self.human_history + prompt
            self.message_list.append(new_message)

            # Store the latest request
            self.latest_request = prompt

            # Generate a response using the OpenAI GPT-3.5 language model
            response = generate_gpt_response(self.message_list)

            # Add the response to the all responses' history
            self.ai_history = self.ai_history + response

            # Print the length of the AI and human conversation history and total conversation history
            print("ai:", len(self.ai_history), "human: ", len(self.human_history), "total: ", len(self.chat_history))

            # If the conversation history is longer than half the CONCISE_THRESHOLD, create a concise history
            if len(self.chat_history) > CONCISE_THRESHOLD / 2:
                t = threading.Thread(target=self.concise_history, daemon=True)
                t.start()

        except Exception as e:
            print(e)
            response = "No Response from GPT."

            if len(self.chat_history) > CONCISE_THRESHOLD:
                self.chat_history = self.task_description + self.slim_history
                sent_prompt = self.chat_history + prompt
                new_message = {"role": ROLE_HUMAN, "content": sent_prompt}
                self.message_list = [new_message, ]
                response = generate_gpt_response(self.message_list)
        finally:
            # Store response
            self.store(role=ROLE_AI, text=response)
            self.append_chat_history(response)
            return response

    def concise_history(self):
        try:
            # Set up the prompt
            task_type = "concise_history"
            prompt = load_task_description(task_type)
            if len(self.chat_history) < CONCISE_THRESHOLD:
                self.slim_history = self.chat_history
            else:
                self.slim_history = self.slim_history + self.latest_request
            sent_prompt = prompt + '"' + self.slim_history + '"'
            if len(sent_prompt) > CONCISE_THRESHOLD:
                sent_prompt = sent_prompt[-CONCISE_THRESHOLD:-1]

            # Generate a response
            new_message = [{"role": ROLE_HUMAN, "content": str(sent_prompt.rstrip())}]
            time.sleep(1)
            print("\nSlim Sent Prompt: \n", sent_prompt, "\n******\n")
            response = generate_gpt_response(new_message)

            self.slim_history = response.lstrip()
            self.store(role=ROLE_AI, text=self.slim_history, path=self.slim_history_file_name)
            print("\nslim stored: ", self.slim_history)

        except Exception as e:
            print("concise error: ", e)
