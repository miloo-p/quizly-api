"""Tests for the quizzes_app."""

import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Quiz
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


def build_fake_quiz():
    """Returns the dict create_quiz_data() would deliver, without any download or AI call."""
    questions = [
        {
            "question_title": f"Question {number}?",
            "question_options": ["A", "B", "C", "D"],
            "answer": "A",
        }
        for number in range(1, 11)
    ]
    return {"title": "Fake Quiz", "description": "Fake description", "questions": questions}


@patch("quizzes_app.api.views.create_quiz_data")
class CreateQuizTests(APITestCase):
    """Tests for POST /api/quizzes/ with the AI chain replaced by a mock."""

    url = "/api/quizzes/"
    video_url = "https://www.youtube.com/watch?v=YE7VzlLtp-4"

    def setUp(self):
        """Creates a user and logs in, so the client holds the token cookies."""
        self.user = User.objects.create_user(username="testuser", password="testpassword123")
        login_data = {"username": "testuser", "password": "testpassword123"}
        self.client.post("/api/login/", login_data, format="json")

    def post_url(self, url):
        """Posts a quiz request with the given YouTube URL."""
        return self.client.post(self.url, {"url": url}, format="json")

    def test_valid_url_returns_201_in_doc_format(self, mock_chain):
        """A valid URL returns 201 with exactly the keys from the doc."""
        mock_chain.return_value = build_fake_quiz()
        response = self.post_url(self.video_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        quiz_keys = {
            "id",
            "title",
            "description",
            "created_at",
            "updated_at",
            "video_url",
            "questions",
        }
        self.assertEqual(set(response.data.keys()), quiz_keys)
        self.assertEqual(response.data["video_url"], self.video_url)
        self.assertEqual(len(response.data["questions"]), 10)
        question_keys = {
            "id",
            "question_title",
            "question_options",
            "answer",
            "created_at",
            "updated_at",
        }
        self.assertEqual(set(response.data["questions"][0].keys()), question_keys)

    def test_quiz_is_saved_for_the_logged_in_user(self, mock_chain):
        """The quiz belongs to the logged-in user and has 10 questions in the database."""
        mock_chain.return_value = build_fake_quiz()
        self.post_url(self.video_url)
        quiz = Quiz.objects.get()
        self.assertEqual(quiz.user, self.user)
        self.assertEqual(quiz.title, "Fake Quiz")
        self.assertEqual(quiz.questions.count(), 10)

    def test_invalid_url_returns_400_without_calling_the_chain(self, mock_chain):
        """A non-YouTube URL is rejected before any download starts."""
        response = self.post_url("https://vimeo.com/123456")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_chain.assert_not_called()

    def test_missing_url_returns_400(self, mock_chain):
        """A request without url is rejected."""
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_chain.assert_not_called()

    def test_without_login_returns_401(self, mock_chain):
        """Without token cookies the user is not authenticated."""
        self.client.cookies.clear()
        response = self.post_url(self.video_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        mock_chain.assert_not_called()

    def test_chain_error_creates_no_quiz(self, mock_chain):
        """If download, Whisper or Gemini fails, an error comes back and nothing is saved."""
        mock_chain.side_effect = ValueError("Gemini did not answer")
        self.client.raise_request_exception = False
        response = self.post_url(self.video_url)
        self.assertIn(
            response.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR],
        )
        self.assertEqual(Quiz.objects.count(), 0)

    def test_broken_question_saves_no_half_quiz(self, mock_chain):
        """If one question cannot be saved, the quiz and the other questions are rolled back."""
        fake_quiz = build_fake_quiz()
        del fake_quiz["questions"][-1]["question_title"]
        mock_chain.return_value = fake_quiz
        self.client.raise_request_exception = False
        self.post_url(self.video_url)
        self.assertEqual(Quiz.objects.count(), 0)
