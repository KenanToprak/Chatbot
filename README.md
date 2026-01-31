Simple Learning Chatbot
A Python-based chatbot that learns from user interactions. It uses JSON for data persistence and the difflib library to find the closest matches to user questions. If the bot doesn't know an answer, it asks the user to teach it, expanding its knowledge base dynamically.

 Features
Persistent Memory: Saves and loads questions/answers from a database.json file.

Fuzzy Matching: Uses get_close_matches to understand questions even if they have typos.

Self-Learning: Directly learns new responses from the user during the chat.

Portable Paths: Uses the os module to automatically handle file paths regardless of the operating system.

 Requirements
Python 3.x

No external libraries required (json, os, and difflib are part of the Python Standard Library).

 Project Structure
main.py: The core logic of the chatbot.

database.json: The storage file where the bot's knowledge is kept (automatically created on first run).

 How to Use
Type your question in the terminal.

If the bot doesn't know the answer, type the response you want it to learn.

Type skip if you don't want to teach that specific question.

Type exit to close the program.
