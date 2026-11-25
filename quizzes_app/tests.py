"""Tests for the quizzes_app."""

import json

from django.test import SimpleTestCase

from .utils import is_valid_youtube_url, parse_quiz_response


class YoutubeUrlTests(SimpleTestCase):
    """Tests for is_valid_youtube_url()."""

    def test_watch_url_is_valid(self):
        """A normal youtube.com/watch?v=... link is accepted."""
        self.assertTrue(is_valid_youtube_url("https://www.youtube.com/watch?v=YE7VzlLtp-4"))

    def test_watch_url_with_extra_params_is_valid(self):
        """Extra query parameters like a timestamp do not matter."""
        self.assertTrue(is_valid_youtube_url("https://www.youtube.com/watch?v=YE7VzlLtp-4&t=42s"))

    def test_invalid_urls_are_rejected(self):
        """Other domains, a missing video id and non-URLs are rejected."""
        invalid_urls = [
            "",
            "not a url",
            "https://vimeo.com/123456",
            "https://www.youtube.com/",
            "https://www.youtube.com/watch",
            "https://evil.com/watch?v=YE7VzlLtp-4",
        ]
        for url in invalid_urls:
            with self.subTest(url=url):
                self.assertFalse(is_valid_youtube_url(url))


class ParseQuizResponseTests(SimpleTestCase):
    """Tests for parse_quiz_response()."""

    def build_quiz(self, question_count=10):
        """Returns a quiz dict in the format Gemini should deliver."""
        question = {
            "question_title": "Question?",
            "question_options": ["A", "B", "C", "D"],
            "answer": "A",
        }
        return {
            "title": "Title",
            "description": "Description",
            "questions": [question] * question_count,
        }

    def test_valid_json_returns_dict_with_10_questions(self):
        """Valid JSON becomes a dict with title, description and 10 questions."""
        quiz = parse_quiz_response(json.dumps(self.build_quiz()))
        self.assertEqual(quiz["title"], "Title")
        self.assertEqual(quiz["description"], "Description")
        self.assertEqual(len(quiz["questions"]), 10)

    def test_broken_json_raises_value_error(self):
        """Text that is not JSON raises a ValueError."""
        with self.assertRaises(ValueError):
            parse_quiz_response("this is not json {")

    def test_wrong_question_count_raises_value_error(self):
        """A quiz with fewer than 10 questions raises a ValueError."""
        with self.assertRaises(ValueError):
            parse_quiz_response(json.dumps(self.build_quiz(question_count=9)))
