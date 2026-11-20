"""Simple learning CLI chatbot backed by a JSON knowledge base."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from difflib import get_close_matches
from typing import Any, Callable

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "database.json")


def _default_database() -> dict[str, list[dict[str, str]]]:
    """Return an empty chatbot knowledge base structure."""
    return {"questions": []}


def load_database(
    data_path: str | os.PathLike[str] = DATA_PATH,
) -> dict[str, list[dict[str, str]]]:
    """Load and validate the JSON knowledge base from ``data_path``.

    Falls back to an empty knowledge base if the file does not exist, cannot
    be read, contains invalid JSON, or does not match the expected schema.
    """
    path = os.fspath(data_path)
    if not os.path.exists(path):
        return _default_database()

    try:
        with open(path, "r", encoding="utf-8") as file:
            raw_data: Any = json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        print(
            f"Warning: Could not load database from {path}: {exc}",
            file=sys.stderr,
        )
        return _default_database()

    if not isinstance(raw_data, dict) or not isinstance(raw_data.get("questions"), list):
        print(
            f"Warning: Invalid database schema in {path}; starting with empty knowledge base.",
            file=sys.stderr,
        )
        return _default_database()

    valid_entries: list[dict[str, str]] = []
    for entry in raw_data["questions"]:
        if (
            isinstance(entry, dict)
            and isinstance(entry.get("question"), str)
            and isinstance(entry.get("answer"), str)
        ):
            valid_entries.append(
                {
                    "question": entry["question"],
                    "answer": entry["answer"],
                }
            )

    return {"questions": valid_entries}


def save_to_database(
    data: dict[str, list[dict[str, str]]],
    data_path: str | os.PathLike[str] = DATA_PATH,
) -> bool:
    """Atomically write ``data`` to ``data_path`` as UTF-8 JSON.

    Returns ``True`` on success or ``False`` if an ``OSError`` occurs.
    """
    target_path = os.fspath(data_path)
    target_dir = os.path.dirname(os.path.abspath(target_path)) or "."
    tmp_path: str | None = None

    try:
        os.makedirs(target_dir, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=target_dir,
            prefix=".database_",
            suffix=".tmp",
            delete=False,
        ) as tmp_file:
            tmp_path = tmp_file.name
            json.dump(data, tmp_file, indent=2, ensure_ascii=False)
            tmp_file.flush()
        os.replace(tmp_path, target_path)
        return True
    except OSError as exc:
        print(
            f"Warning: Could not save database to {target_path}: {exc}",
            file=sys.stderr,
        )
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        return False


def find_best_match(user_question: str, questions: list[str]) -> str | None:
    """Return the closest matching question using case-insensitive fuzzy matching."""
    normalized_query = user_question.strip().lower()
    if not normalized_query:
        return None

    normalized_to_original: dict[str, str] = {}
    for q in questions:
        if not isinstance(q, str):
            continue
        norm = q.strip().lower()
        if norm and norm not in normalized_to_original:
            normalized_to_original[norm] = q

    if not normalized_to_original:
        return None

    matches = get_close_matches(
        normalized_query,
        list(normalized_to_original.keys()),
        n=1,
        cutoff=0.6,
    )
    return normalized_to_original[matches[0]] if matches else None


def get_answer_for_question(
    question: str,
    database: dict[str, list[dict[str, str]]],
) -> str | None:
    """Look up the answer for ``question`` in ``database`` case-insensitively."""
    normalized_target = question.strip().lower()
    if not normalized_target:
        return None

    for q_a in database.get("questions", []):
        stored_q = q_a.get("question")
        if isinstance(stored_q, str) and stored_q.strip().lower() == normalized_target:
            return q_a.get("answer")
    return None


def _upsert_question(
    database: dict[str, list[dict[str, str]]],
    question: str,
    answer: str,
) -> None:
    """Insert or update a normalized question-answer pair without duplicates."""
    normalized_q = question.strip().lower()
    for q_a in database["questions"]:
        if q_a["question"].strip().lower() == normalized_q:
            q_a["question"] = normalized_q
            q_a["answer"] = answer
            return
    database["questions"].append({"question": normalized_q, "answer": answer})


def chat_bot(
    data_path: str | os.PathLike[str] = DATA_PATH,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> None:
    """Run the interactive chatbot read-eval-learn loop."""
    database = load_database(data_path=data_path)

    while True:
        try:
            user_input = input_fn("You: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            output_fn("\nBot: Goodbye!")
            break

        if not user_input:
            continue

        if user_input == "exit":
            output_fn("Bot: Goodbye!")
            break

        questions_list = [q_a["question"] for q_a in database["questions"]]
        best_match = find_best_match(user_input, questions_list)

        if best_match:
            answer = get_answer_for_question(best_match, database)
            output_fn(f"Bot: {answer}")
        else:
            output_fn("Bot: I don't know the answer to that. Can you teach me?")
            try:
                new_answer = input_fn("Type the answer or 'skip' to ignore: ").strip()
            except (EOFError, KeyboardInterrupt):
                output_fn("\nBot: Goodbye!")
                break

            if not new_answer or new_answer.lower() == "skip":
                continue

            _upsert_question(database, user_input, new_answer)
            if save_to_database(database, data_path=data_path):
                output_fn("Bot: Thank you!")


if __name__ == "__main__":
    chat_bot()
