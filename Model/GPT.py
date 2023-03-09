import openai


class GPT:
    def setup_chat_gpt(self, task_type):
        self.task_description = load_task_description(task_type)
        self.chat_history = self.task_description
        self.human_history = self.task_description
        self.ai_history = self.task_description
        initial_message = {"role": ROLE_SYSTEM, "content": self.task_description}
        self.message_list.append(initial_message)


def generate_gpt_response(sent_prompt, max_tokens=1000, temperature=0.3, id_idx=0):
    try:
        if id_idx == 0:
            openai.api_key = "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"
        else:
            openai.api_key = "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"
        model_engine = "gpt-3.5-turbo"
        print("\n********\nSent Prompt:", sent_prompt, "\n*********\n")
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
