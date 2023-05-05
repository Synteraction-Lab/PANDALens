import time

# Load the labels from the coco.names file
with open('coco.names', 'r') as f:
    classes = [line.strip() for line in f.readlines()]

# Define a dictionary of questions and corresponding COCO class IDs
questions = {
    "Do you enjoy visiting historic landmarks?": [0, 14, 15, 16, 17, 18],
    "Are you interested in seeing animals in their natural habitat?": [13, 19, 20, 21, 22, 23, 24, 25],
    "Do you like to relax on the beach?": [32, 33, 34, 35, 36],
    "Are you a foodie who loves trying new cuisines?": [39, 40, 41, 42, 43, 44, 46],
    "Do you enjoy outdoor activities like hiking or rock climbing?": [67, 68, 69, 70, 71, 72, 73, 74, 75, 76],
}

# Define an empty list to store the user's selected COCO class IDs
interests = []

# Ask the user each question and add the relevant COCO class IDs to the interests list
print("Please answer the following questions about your travel preferences:")
for question in questions:
    answer = input(f"{question} (y/n) ").lower()
    if answer == 'y':
        interests.extend(questions[question])
    time.sleep(0.5) # pause for half a second to prevent rapid-fire questions

# Filter out any duplicate COCO class IDs and sort the interests list by ID
interests = list(set(interests))
interests.sort()

# Print the list of interests to the console
interest_labels = [classes[i] for i in interests]
print("Your interests include:")
print(interests)
print(interest_labels)