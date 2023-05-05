import os
import threading
import time
from datetime import datetime

import openai
import tiktoken

from Storage.reader import load_task_description
from Storage.writer import append_json_data
from Utilities.constant import ALL_HISTORY, ROLE_SYSTEM, CONCISE_THRESHOLD, ROLE_HUMAN, ROLE_AI

API_KEYS = ["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",
            "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"]
MAX_TOKENS = 1000
TEMPERATURE = 0.3


def num_tokens_from_messages(messages, model="gpt-3.5-turbo"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo":
        print("Warning: gpt-3.5-turbo may change over time. Returning num tokens assuming gpt-3.5-turbo-0301.")
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301")
    elif model == "gpt-4":
        print("Warning: gpt-4 may change over time. Returning num tokens assuming gpt-4-0314.")
        return num_tokens_from_messages(messages, model="gpt-4-0314")
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif model == "gpt-4-0314":
        tokens_per_message = 3
        tokens_per_name = 1
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


def generate_gpt_response(sent_prompt, max_tokens=MAX_TOKENS, temperature=TEMPERATURE, api_key_idx=0):
    try:
        openai.api_key = API_KEYS[api_key_idx]
        model_engine = "gpt-3.5-turbo"
        response = openai.ChatCompletion.create(
            model=model_engine,
            messages=sent_prompt,
            max_tokens=max_tokens,
            n=1,
            stop=None,
            temperature=temperature,
        )
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
        self.message_list = []

        self.send_history_mode = ALL_HISTORY

        self.chat_history_file_name = chat_history_file_name
        self.slim_history_file_name = slim_history_file_name

    def setup_chat_gpt(self, task_type):
        self.task_description = load_task_description(task_type)
        self.chat_history = self.task_description
        self.human_history = ""
        self.ai_history = ""
        initial_message = {"role": ROLE_SYSTEM, "content": self.task_description}
        self.message_list.append(initial_message)

    def store(self, role=ROLE_HUMAN, text=None, path=None):
        if path is None:
            path = self.chat_history_file_name
        data = {"time": str(datetime.now()), "role": role, "content": text.lstrip()}
        append_json_data(path, data)

    def resume_stored_history(self):
        file_name = self.slim_history_file_name if os.path.isfile(
            self.slim_history_file_name) else self.chat_history_file_name
        with open(file_name) as f:
            chat_history = f.read()
            print("Resuming the conversation:", file_name)
        self.process_prompt_and_get_gpt_response(command=chat_history,
                                                 prefix="Resume the conversation history\
                                                             (Don't show the timestamp in the following answers)",
                                                 is_prompt_stored=False)

    def append_chat_history(self, response):
        self.chat_history += response

    def process_prompt_and_get_gpt_response(self, command, is_prompt_stored=True, role=ROLE_HUMAN, prefix=""):
        response = ""

        prompt = f"{role} : {prefix}{command}"
        new_message = {"role": role, "content": f"{prefix}{command}"}
        if is_prompt_stored:
            self.store(role=role, text=prompt)
            print(prompt)
        try:
            self.chat_history += prompt
            self.human_history += prompt
            self.message_list.append(new_message)

            self.latest_request = prompt

            response = generate_gpt_response(self.message_list)

            self.ai_history += response

            print("total token count:", num_tokens_from_messages(self.message_list))

            if num_tokens_from_messages(self.message_list) > CONCISE_THRESHOLD / 2:
                t = threading.Thread(target=self.concise_history, daemon=True)
                t.start()

        except Exception as e:
            print(e)
            response = "No Response from GPT."

            if num_tokens_from_messages(self.message_list) > CONCISE_THRESHOLD:
                self.chat_history = self.task_description + self.slim_history

                # Combine important moments with the last few messages
                last_messages = self.message_list[-2:]
                self.message_list = [{"role": ROLE_SYSTEM, "content": prompt}] \
                                    + [{"role": ROLE_HUMAN, "content": f"Here is concise chat context: {response}"}] \
                                    + last_messages + [new_message]

                response = generate_gpt_response(self.message_list)
        finally:
            self.store(role=ROLE_AI, text=response)
            self.append_chat_history(response)
            return response

    def concise_history(self):
        try:
            # Set up the prompt
            task_type = "concise_history"
            prompt = load_task_description(task_type)

            if num_tokens_from_messages(self.message_list) < CONCISE_THRESHOLD:
                self.slim_history = self.chat_history
            else:
                self.slim_history = self.slim_history + self.latest_request

            if len(self.slim_history) > CONCISE_THRESHOLD * 4 - 50:
                self.slim_history = self.slim_history[-(CONCISE_THRESHOLD * 4 - 50):-1]

            # Include the content to be summarized
            sent_prompt = f"{prompt} Here is the chat history to be summarized:\n\n{self.slim_history}"

            if len(sent_prompt) > CONCISE_THRESHOLD * 4:
                sent_prompt = sent_prompt[-CONCISE_THRESHOLD * 4:-1]

            # Generate a response
            new_message = [{"role": ROLE_HUMAN, "content": str(sent_prompt.rstrip())}]
            time.sleep(1)
            print("\nSlim Sent Prompt: \n", sent_prompt, "\n******\n")
            response = generate_gpt_response(new_message)

            self.slim_history = response.lstrip()
            self.store(role=ROLE_AI, text=self.slim_history, path=self.slim_history_file_name)

        except Exception as e:
            print("concise error: ", e)


if __name__ == "__main__":
    gpt = GPT("data/chat_history.json", "data/slim_history.json")
    gpt.setup_chat_gpt("travel_blog")

    # Simulating multiple user inputs
    user_inputs = [
        {
            "no": 1,
            "label": "Coffee 94% Cafe 92% Beverage 90% Table 88% Interior 86% Latte 84% Morning 82% Breakfast 80% Food 78% Relaxation 76%",
            "Caption": "A cup of coffee on a wooden table in a cozy cafe",
            "Audio": "soft music, low chatter, espresso machine noises",
            "comment": "Starting my day with a delicious cup of coffee at this lovely cafe!",
            "user behaviors": "the user is sipping coffee and looking out the window"
        },
        {
            "no": 2,
            "label": "Park 95% Trees 93% Grass 91% Outdoor 89% Green 87% Nature 85% Bench 83% Path 81% Walk 79% Recreation 77% Relaxation 75%",
            "Caption": "A lush green park with a walking path and benches",
            "Audio": "birds chirping, children playing, leaves rustling",
            "comment": "Taking a relaxing morning walk through the park, enjoying the fresh air!",
            "user behaviors": "the user is strolling along the path, occasionally stopping to admire the scenery"
        },
        {
            "no": 3,
            "label": "Museum 94% Art 92% Gallery 90% Exhibition 88% Painting 86% Sculpture 84% Culture 82% Education 80% History 78% Contemporary 76% Masterpiece 74%",
            "Caption": "An art gallery with a large painting on the wall",
            "Audio": "footsteps echoing, hushed conversations",
            "comment": "Exploring the local museum, such amazing artwork on display!",
            "user behaviors": "the user is closely examining the paintings and sculptures"
        },
        {
            "no": 4,
            "label": "Market 95% Street 93% Food 91% Stalls 89% Shopping 87% Culture 85% People 83% Local 81% Produce 79% Vendors 77% Outdoor 75%",
            "Caption": "A bustling street market with various food stalls",
            "Audio": "vendors shouting, sizzling sounds, people talking",
            "comment": "Checking out the street market for a tasty lunch, so many options!",
            "user behaviors": "the user is trying different foods and chatting with vendors"
        },
        {
            "no": 5,
            "label": "Beach 95% Sand 93% Ocean 91% Vacation 88% Travel 86% Sea 84% Leisure 82% Relaxation 80% Sun 78% Coast 76% Shore 74% Summer 72% Waves 70% People 68%",
            "Caption": "A beautiful sandy beach with people relaxing and playing",
            "Audio": "ocean waves crashing, laughter, seagulls calling",
            "comment": "Spending the afternoon at the beach, soaking up the sun and enjoying the waves!",
            "user behaviors": "the user is sunbathing and occasionally going for a swim"
        },
        {
            "no": 6,
            "label": "Restaurant 95% Food 93% Dining 90% Interior 88% Table 85% Chairs 83% Decor 81% Atmosphere 79% Gourmet 77% Delicious 75% Meal 73% Cuisine 71%",
            "Caption": "A beautifully decorated restaurant with dim lighting",
            "Audio": "soft music, clinking of glasses, people talking",
            "comment": "Having a fantastic dinner at this elegant restaurant!",
            "user behaviors": "the user is using a fork to cut a piece of food and placing it in their mouth"
        },
        {
            "no": 7,
            "label": "City 96% Skyline 94% Urban 92% Architecture 90% Skyscraper 88% Night 86% Lights 84% Modern 82% Travel 80% Downtown 78% Buildings 76% Reflection 74% River 72%",
            "Caption": "A stunning city skyline at night with a river in the foreground",
            "Audio": "ambient city noises, distant car honks",
            "comment": "This city is breathtaking at night, the skyline looks like a postcard!",
            "user behaviors": "the user is taking multiple pictures and pointing at a specific building"
        },
        {
            "no": 8,
            "label": "Concert 94% Music 92% Stage 90% Performance 88% Band 86% Audience 84% Lights 82% Entertainment 80% Singing 78% Live 76% Event 74% Party 72%",
            "Caption": "A lively concert with a band performing on stage",
            "Audio": "loud music, cheering, clapping",
            "comment": "Ending the night with an awesome concert, the atmosphere is incredible!",
            "user behaviors": "the user is dancing and singing along to the music"
        }
    ]

    for user_input in user_inputs:
        response = gpt.process_prompt_and_get_gpt_response(command=str(user_input))
        print("GPT Response:", response)
