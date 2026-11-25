"""Tests for the auth_app API endpoints."""

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


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


class LoginTests(APITestCase):
    """Tests for POST /api/login/."""

    url = "/api/login/"

    def setUp(self):
        """Creates a user and a valid login body as in the API doc."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword123"
        )
        self.data = {"username": "testuser", "password": "testpassword123"}

    def test_valid_login_returns_200_with_detail_and_user(self):
        """Valid credentials return 200 with detail and the user data from the doc."""
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "Login successfully!")
        expected_user = {"id": self.user.id, "username": "testuser", "email": "test@example.com"}
        self.assertEqual(response.data["user"], expected_user)

    def test_valid_login_sets_httponly_token_cookies(self):
        """Login sets access_token and refresh_token as HttpOnly cookies."""
        response = self.client.post(self.url, self.data, format="json")
        for name in ["access_token", "refresh_token"]:
            self.assertIn(name, response.cookies)
            self.assertTrue(response.cookies[name]["httponly"])

    def test_tokens_are_not_in_response_body(self):
        """The tokens are only sent as cookies, not in the JSON body."""
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(set(response.data.keys()), {"detail", "user"})

    def test_wrong_password_returns_401(self):
        """A wrong password is rejected with 401."""
        self.data["password"] = "wrongpassword"
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unknown_username_returns_401(self):
        """An unknown username is rejected with 401."""
        self.data["username"] = "nobody"
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cookies_contain_valid_tokens_of_the_user(self):
        """The cookies hold a real access and refresh token of the logged-in user."""
        response = self.client.post(self.url, self.data, format="json")
        access = AccessToken(response.cookies["access_token"].value)
        refresh = RefreshToken(response.cookies["refresh_token"].value)
        self.assertEqual(access["user_id"], str(self.user.id))
        self.assertEqual(refresh["user_id"], str(self.user.id))


class TokenRefreshTests(APITestCase):
    """Tests for POST /api/token/refresh/."""

    url = "/api/token/refresh/"

    def setUp(self):
        """Creates a user and logs in, so the client holds both token cookies."""
        self.user = User.objects.create_user(username="testuser", password="testpassword123")
        login_data = {"username": "testuser", "password": "testpassword123"}
        self.client.post("/api/login/", login_data, format="json")

    def test_refresh_returns_200_with_detail(self):
        """A valid refresh_token cookie returns 200 and the message from the doc."""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"detail": "Token refreshed"})

    def test_refresh_sets_new_httponly_access_cookie(self):
        """The response sets a new valid access token of the user as HttpOnly cookie."""
        response = self.client.post(self.url)
        self.assertTrue(response.cookies["access_token"]["httponly"])
        access = AccessToken(response.cookies["access_token"].value)
        self.assertEqual(access["user_id"], str(self.user.id))

    def test_missing_refresh_cookie_returns_401(self):
        """Without a refresh_token cookie the request is rejected with 401."""
        del self.client.cookies["refresh_token"]
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_refresh_cookie_returns_401(self):
        """An invalid refresh_token cookie is rejected with 401."""
        self.client.cookies["refresh_token"] = "invalid-token"
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_token_as_refresh_cookie_returns_401(self):
        """An access token in the refresh_token cookie is rejected with 401."""
        self.client.cookies["refresh_token"] = self.client.cookies["access_token"].value
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
