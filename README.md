# Quizly Backend

REST API for Quizly, an app that turns a YouTube video into a quiz with 10 multiple-choice questions.
Built with Django and Django REST Framework, JWT authentication in HttpOnly cookies and SQLite.
The quizzes are created by an AI pipeline with yt-dlp, Whisper and Google Gemini.

## Status

- [x] Registration, login, token refresh and logout
- [x] Quiz and Question models (also visible in `/admin/`)
- [x] AI pipeline in `quizzes_app/utils.py`, with tests
- [ ] Quiz endpoints: create from a YouTube URL, list, read, update, delete

## How a quiz is created

1. yt-dlp downloads the audio track of the video into a temporary folder.
2. Whisper transcribes the audio locally. The folder is deleted afterwards.
3. Gemini turns the transcript into a title, a short description and 10 questions with 4 options each, returned as JSON.
4. The response is checked: it must be valid JSON with exactly 10 questions.

## Requirements

- Python 3.12 or newer
- Git
- [FFmpeg](https://ffmpeg.org/download.html) on your PATH (Whisper uses it to read audio)
- A Gemini API key from Google AI Studio

## Installation

1. Clone the repository and open the folder:

   ```bash
   git clone https://github.com/miloo-p/quizly-api.git
   cd quizly-api
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   ```

   Windows:

   ```bash
   .venv\Scripts\activate
   ```

   macOS / Linux:

   ```bash
   source .venv/bin/activate
   ```

3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

   This also installs PyTorch for Whisper and can take a while.

4. Create the `.env` file from the example:

   Windows:

   ```bash
   copy .env.example .env
   ```

   macOS / Linux:

   ```bash
   cp .env.example .env
   ```

   Generate a secret key:

   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

   Open `.env`, paste the key behind `SECRET_KEY=` and your Gemini API key behind `GEMINI_API_KEY=`.

5. Create the database:

   ```bash
   python manage.py migrate
   ```

6. Optional: create an admin user to see quizzes and questions in `/admin/`:

   ```bash
   python manage.py createsuperuser
   ```

7. Start the server:

   ```bash
   python manage.py runserver
   ```

   The API is now available at `http://127.0.0.1:8000/api/`.

## Running the tests

```bash
python manage.py test
```

The tests need no Gemini key and no network access.

## Notes

- Authentication uses JWTs in HttpOnly cookies (`access_token`, `refresh_token`). The tokens are never part of the response body.
- Registration, login and token refresh work without login. All other endpoints need a valid `access_token` cookie.
- Login uses `username` and `password`. Each email address can only be registered once, a duplicate returns `400 Bad Request`.
- Logout needs both cookies. It blacklists the refresh token and deletes both cookies.
- CORS allows frontends on `localhost` and `127.0.0.1`, ports `4200` and `5500`. Use the same host for frontend and API
  (both `127.0.0.1` or both `localhost`). The cookies are `SameSite=Lax`, so the browser blocks them between the two.
- Only YouTube links like `https://www.youtube.com/watch?v=<id>` are accepted (also `youtube.com` and `m.youtube.com`).
  Short links (`youtu.be`) are not.
- Whisper runs locally with the `base` model, which is downloaded on first use (about 140 MB).
- The Gemini model is set in `core/settings.py` (`GEMINI_MODEL`).

## Endpoints

| Method | URL                   | Description                             |
| ------ | --------------------- | --------------------------------------- |
| POST   | `/api/register/`      | Register a user                         |
| POST   | `/api/login/`         | Log in and receive the token cookies    |
| POST   | `/api/token/refresh/` | Get a new access token cookie           |
| POST   | `/api/logout/`        | Log out and blacklist the refresh token |
