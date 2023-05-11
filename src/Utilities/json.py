def detect_json(string):
    start_index = string.find('{')
    end_index = string.rfind('}')
    if start_index == -1 or end_index == -1 or start_index > end_index:
        return None
    try:
        return json.loads(string[start_index:end_index + 1])
    except ValueError:
        return None


if __name__ == '__main__':
    string = """{
    "mode": "authoring", 
    "response":{
        "summary of newly added content": "[snippet of the travel blog content preview in first person narration]", 
        "question to users": "[question to help them provide deeper and more interesting content *if necessary*, return 'None' when no question you want to ask.]"
        }
    }"""



    result = detect_json(string)

    if result is None:
        print("The input string does not contain a valid JSON")
    else:
        print("The parsed JSON object is:")
        print(result)
