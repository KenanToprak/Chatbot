"""Unit tests for Chatbot."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from unittest.mock import patch

import Chatbot


class TestDatabasePersistence(unittest.TestCase):
    def test_load_database_returns_empty_when_file_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "missing.json")
            self.assertEqual(Chatbot.load_database(db_path), {"questions": []})

    def test_load_database_handles_corrupt_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "corrupt.json")
            with open(db_path, "w", encoding="utf-8") as fh:
                fh.write("{not valid json")
            self.assertEqual(Chatbot.load_database(db_path), {"questions": []})

    def test_load_database_handles_invalid_schema_and_filters_bad_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "bad_schema.json")
            with open(db_path, "w", encoding="utf-8") as fh:
                json.dump(["not", "a", "dict"], fh)
            self.assertEqual(Chatbot.load_database(db_path), {"questions": []})

            with open(db_path, "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "questions": [
                            {"question": "Hi", "answer": "Hello"},
                            {"question": 123, "answer": "bad"},
                            "not-a-dict",
                        ]
                    },
                    fh,
                )
            self.assertEqual(
                Chatbot.load_database(db_path),
                {"questions": [{"question": "Hi", "answer": "Hello"}]},
            )

    def test_save_to_database_atomic_persistence_and_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "nested", "db.json")
            payload = {
                "questions": [{"question": "merhaba", "answer": "günaydın"}]
            }
            self.assertTrue(Chatbot.save_to_database(payload, data_path=db_path))
            self.assertEqual(Chatbot.load_database(db_path), payload)
            leftovers = [f for f in os.listdir(os.path.dirname(db_path)) if f.endswith(".tmp")]
            self.assertEqual(leftovers, [])

    def test_save_to_database_handles_os_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "db.json")
            with patch("Chatbot.os.replace", side_effect=OSError("disk error")):
                ok = Chatbot.save_to_database({"questions": []}, data_path=db_path)
            self.assertFalse(ok)


class TestMatching(unittest.TestCase):
    def test_find_best_match_and_get_answer_are_case_insensitive(self) -> None:
        database = {
            "questions": [
                {"question": "HELLO", "answer": "Hi there!"},
                {"question": "How Are You?", "answer": "Doing well."},
            ]
        }
        questions = [entry["question"] for entry in database["questions"]]
        match = Chatbot.find_best_match("hello", questions)
        self.assertEqual(match, "HELLO")
        self.assertEqual(
            Chatbot.get_answer_for_question(match or "", database),
            "Hi there!",
        )
        self.assertEqual(
            Chatbot.get_answer_for_question("how are you?", database),
            "Doing well.",
        )

    def test_find_best_match_rejects_empty_and_unrelated(self) -> None:
        self.assertIsNone(Chatbot.find_best_match("", ["hello"]))
        self.assertIsNone(Chatbot.find_best_match("   ", ["hello"]))
        self.assertIsNone(Chatbot.find_best_match("zzzzzzzz", ["hello"]))


class TestChatBotLoop(unittest.TestCase):
    def _run_loop(
        self,
        inputs: list[object],
        initial_data: dict | None = None,
    ) -> tuple[list[str], dict]:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "database.json")
            if initial_data is not None:
                Chatbot.save_to_database(initial_data, data_path=db_path)

            it = iter(inputs)
            outputs: list[str] = []

            def fake_input(prompt: str) -> str:
                nxt = next(it)
                if isinstance(nxt, BaseException):
                    raise nxt
                return str(nxt)

            Chatbot.chat_bot(
                data_path=db_path,
                input_fn=fake_input,
                output_fn=outputs.append,
            )
            saved = Chatbot.load_database(db_path)
            return outputs, saved

    def test_ignores_empty_input_skip_whitespace_and_blank_answers(self) -> None:
        outputs, saved = self._run_loop(
            [
                "",
                "   ",
                "unknown question",
                "  skip  ",
                "another unknown",
                "   ",
                "exit",
            ]
        )
        self.assertEqual(saved, {"questions": []})
        self.assertEqual(
            outputs,
            [
                "Bot: I don't know the answer to that. Can you teach me?",
                "Bot: I don't know the answer to that. Can you teach me?",
                "Bot: Goodbye!",
            ],
        )

    def test_teaches_persists_and_answers_mixed_case(self) -> None:
        outputs, saved = self._run_loop(
            ["What is Python?", "  A programming language.  ", "what is python?", "exit"]
        )
        self.assertEqual(
            saved,
            {
                "questions": [
                    {
                        "question": "what is python?",
                        "answer": "A programming language.",
                    }
                ]
            },
        )
        self.assertEqual(
            outputs,
            [
                "Bot: I don't know the answer to that. Can you teach me?",
                "Bot: Thank you!",
                "Bot: A programming language.",
                "Bot: Goodbye!",
            ],
        )

    def test_upsert_prevents_duplicate_normalized_questions(self) -> None:
        db = {"questions": [{"question": "Hello", "answer": "Old"}]}
        Chatbot._upsert_question(db, "  HELLO ", "New")
        self.assertEqual(
            db,
            {"questions": [{"question": "hello", "answer": "New"}]},
        )

    def test_eof_and_keyboard_interrupt_exit_gracefully(self) -> None:
        outputs_eof, _ = self._run_loop([EOFError()])
        self.assertEqual(outputs_eof, ["\nBot: Goodbye!"])

        outputs_ki, _ = self._run_loop([KeyboardInterrupt()])
        self.assertEqual(outputs_ki, ["\nBot: Goodbye!"])

        outputs_teach_eof, saved = self._run_loop(["new q", EOFError()])
        self.assertEqual(saved, {"questions": []})
        self.assertEqual(
            outputs_teach_eof,
            [
                "Bot: I don't know the answer to that. Can you teach me?",
                "\nBot: Goodbye!",
            ],
        )


if __name__ == "__main__":
    unittest.main()
