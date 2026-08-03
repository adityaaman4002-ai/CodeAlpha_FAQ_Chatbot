"""
test_chatbot.py
----------------
Basic unit tests for the FAQ chatbot.

Run with:
    pytest tests/
or
    python -m unittest tests.test_chatbot
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from chatbot.matcher import FAQMatcher
from chatbot.preprocess import preprocess


class TestPreprocess(unittest.TestCase):
    def test_lowercases_and_strips_punctuation(self):
        self.assertEqual(preprocess("Hello, World!!!"), "hello world")

    def test_removes_common_stopwords(self):
        result = preprocess("What is the best way to do this")
        self.assertNotIn("the", result.split())
        self.assertNotIn("is", result.split())

    def test_empty_string(self):
        self.assertEqual(preprocess(""), "")

    def test_keeps_question_words(self):
        result = preprocess("How do I do that")
        self.assertIn("how", result.split())


class TestFAQMatcher(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bot = FAQMatcher()

    def test_loads_faqs(self):
        self.assertGreater(len(self.bot.faqs), 0)

    def test_exact_question_match(self):
        result = self.bot.get_response("How do I reset my password?")
        self.assertTrue(result.matched)
        self.assertIn("Forgot Password", result.answer)

    def test_paraphrased_query_still_matches(self):
        result = self.bot.get_response("i forgot my password, how to reset it")
        self.assertTrue(result.matched)
        self.assertEqual(result.category, "Account")

    def test_keyword_only_in_answer_still_matches(self):
        # "paypal" only appears in the FAQ's answer/keywords, not its question text
        result = self.bot.get_response("can I pay with paypal")
        self.assertTrue(result.matched)
        self.assertIn("PayPal", result.answer)

    def test_nonsense_query_falls_back(self):
        result = self.bot.get_response("zzxqq blorpaflorp nonsense query")
        self.assertFalse(result.matched)

    def test_empty_query_handled_gracefully(self):
        result = self.bot.get_response("")
        self.assertFalse(result.matched)

    def test_list_categories(self):
        categories = self.bot.list_categories()
        self.assertIn("Billing", categories)
        self.assertIn("Account", categories)


class TestFlaskAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import app
        cls.client = app.test_client()

    def test_index_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_chat_endpoint_returns_answer(self):
        response = self.client.post("/api/chat", json={"message": "How do I cancel my subscription?"})
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["matched"])
        self.assertIn("Cancel Plan", data["answer"])

    def test_chat_endpoint_handles_missing_message(self):
        response = self.client.post("/api/chat", json={})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.get_json()["matched"])

    def test_categories_endpoint(self):
        response = self.client.get("/api/categories")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.get_json()["categories"], list)


if __name__ == "__main__":
    unittest.main()
