"""Tests for the auth_app API endpoints."""

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase


class RegistrationTests(APITestCase):
    """Tests for POST /api/register/."""

    url = "/api/register/"

    def setUp(self):
        """Builds a valid request body exactly as in the API doc."""
        self.data = {
            "username": "testuser",
            "password": "testpassword123",
            "confirmed_password": "testpassword123",
            "email": "test@example.com",
        }

    def assert_rejected(self, field=None):
        """Posts self.data, expects 400 (with an error for field) and no new user."""
        users_before = User.objects.count()
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        if field:
            self.assertIn(field, response.data)
        self.assertEqual(User.objects.count(), users_before)

    def test_valid_data_returns_201_with_detail(self):
        """Valid data returns 201 and only the message from the doc."""
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {"detail": "User created successfully!"})

    def test_user_is_saved_with_hashed_password(self):
        """The user exists afterwards and the password is not plain text."""
        self.client.post(self.url, self.data, format="json")
        user = User.objects.get(username="testuser")
        self.assertTrue(user.check_password("testpassword123"))
        self.assertNotEqual(user.password, "testpassword123")

    def test_passwords_do_not_match_returns_400(self):
        """Different passwords are rejected."""
        self.data["confirmed_password"] = "otherpassword123"
        self.assert_rejected()

    def test_username_taken_returns_400(self):
        """A username that already exists is rejected."""
        User.objects.create_user(username="testuser", email="other@example.com", password="x")
        self.assert_rejected("username")

    def test_email_taken_returns_400(self):
        """An email that already exists is rejected."""
        User.objects.create_user(username="otheruser", email="test@example.com", password="x")
        self.assert_rejected("email")

    def test_missing_email_returns_400(self):
        """A request without email is rejected."""
        del self.data["email"]
        self.assert_rejected("email")

    def test_blank_email_returns_400(self):
        """An empty email is rejected."""
        self.data["email"] = ""
        self.assert_rejected("email")
