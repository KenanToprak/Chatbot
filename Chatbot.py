import json
import os
from difflib import get_close_matches

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'database.json')

def load_database():
    if not os.path.exists(DATA_PATH):
        return {"questions": []}
    
    with open(DATA_PATH, 'r', encoding='utf-8') as file:
        return json.load(file)

def save_to_database(data):
    with open(DATA_PATH, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

def find_best_match(user_question, questions):
    matches = get_close_matches(user_question, questions, n=1, cutoff=0.6)
    return matches[0] if matches else None

def get_answer_for_question(question, database):
    for q_a in database["questions"]:
        if q_a["question"] == question:
            return q_a["answer"]
    return None

def chat_bot():
    database = load_database()

    while True:
        user_input = input("You: ").strip().lower()
        
        if user_input == "exit":
            break

        questions_list = [q_a["question"] for q_a in database["questions"]]
        best_match = find_best_match(user_input, questions_list)

        if best_match:
            answer = get_answer_for_question(best_match, database)
            print(f"Bot: {answer}")
        else:
            print("Bot: I don't know the answer to that. Can you teach me?")
            new_answer = input("Type the answer or 'skip' to ignore: ")
            
            if new_answer.lower() != 'skip':
                database["questions"].append({
                    "question": user_input,
                    "answer": new_answer
                })
                save_to_database(database)
                print("Bot: Thank you!")

if __name__ == '__main__':
    chat_bot()