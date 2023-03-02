import tiktoken


def num_tokens_from_string(string, encoding_name="text-davinci-003"):
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens
