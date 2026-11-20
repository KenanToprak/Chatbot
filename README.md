# Simple Learning Chatbot

A Python-based CLI chatbot that learns from user interactions. It uses JSON for data persistence and Python's built-in `difflib` library to find the closest matches to user questions. When the bot does not know an answer, it asks the user to teach it and persists the new response.

## Features

- **Persistent Memory**: Loads and atomically saves questions and answers in `database.json`.
- **Fuzzy Matching**: Uses case-insensitive `difflib.get_close_matches` to handle minor typos and capitalization differences.
- **Self-Learning**: Learns new responses interactively during chat without creating duplicate question entries.
- **Safe CLI Handling**: Handles empty inputs, blank/whitespace `skip` responses, malformed/missing `database.json`, and `EOFError` / `KeyboardInterrupt` cleanly.

## Requirements

- Python 3.10+ (uses Python standard library only; no third-party dependencies required)

## Project Structure

- `Chatbot.py`: Core chatbot logic, database load/save helpers, and CLI entrypoint.
- `database.json`: JSON knowledge base (if missing or invalid, the bot starts with an empty in-memory knowledge base and creates/updates `database.json` when you teach it a new answer).
- `tests/test_chatbot.py`: Automated `unittest` suite covering database persistence, matching, and the interactive chat loop.

## How to Run

```bash
python Chatbot.py
```

### Commands During Chat

- Type any question in the terminal and press `Enter`.
- If the bot does not know the answer, type the response you want it to learn.
- Type `skip` (or leave the answer blank) if you do not want to teach that question.
- Type `exit` (or press `Ctrl+C` / `Ctrl+D` / `Ctrl+Z`) to close the program.

## How to Test

```bash
python -m unittest discover -s tests -v
```
