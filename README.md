# Quizly Backend

REST API for Quizly, an app that turns a YouTube video into a quiz with 10 multiple-choice questions.
Built with Django and Django REST Framework, JWT authentication in HttpOnly cookies and SQLite.
The quizzes are created by an AI pipeline with yt-dlp, Whisper and Google Gemini.

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

   If PowerShell refuses to run the activate script ("running scripts is disabled"), allow local scripts once and try again:

   ```bash
   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
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

## Running the frontend

1. Open the Quizly frontend folder in VS Code.
2. Right-click `index.html` and choose **Open with Live Server** (extension "Live Server").
3. Make sure the address bar shows `http://127.0.0.1:5500`, not `localhost`. Otherwise the browser does not send the
   token cookies to the API at `127.0.0.1:8000`.

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
- The Gemini model is set in `core/settings.py`. Default: `GEMINI_MODEL = "gemini-3.5-flash-lite"`.
  To switch, replace the name with another Flash model, for example:
  - `gemini-3.5-flash-lite` (default)
  - `gemini-3.1-flash-lite`
  - `gemini-3.5-flash`
  - `gemini-3.6-flash`
  - `gemini-3.7-flash`
  - `gemini-3.8-flash`

  Which models your API key can use may change over time (older ones like `gemini-2.5-flash` are no longer
  available for new keys). The current list is shown in Google AI Studio.

## Endpoints

| Method | URL                   | Description                             |
| ------ | --------------------- | --------------------------------------- |
| POST   | `/api/register/`      | Register a user                         |
| POST   | `/api/login/`         | Log in and receive the token cookies    |
| POST   | `/api/token/refresh/` | Get a new access token cookie           |
| POST   | `/api/logout/`        | Log out and blacklist the refresh token |
| POST   | `/api/quizzes/`       | Create a quiz from a YouTube URL        |
| GET    | `/api/quizzes/`       | List all quizzes of the user            |
| GET    | `/api/quizzes/{id}/`  | Get one quiz with its questions         |
| PATCH  | `/api/quizzes/{id}/`  | Change title and/or description         |
| DELETE | `/api/quizzes/{id}/`  | Delete a quiz and all its questions     |

## Decisions where the API doc leaves room

- An error in the AI pipeline (download, Whisper or Gemini fails) returns `500` with a `detail` message. Nothing is
  saved in that case, quiz and questions are stored in one transaction.
- A URL that is not a YouTube watch link returns `400` before any download starts.
- `PATCH` only changes `title` and `description`. `video_url` is read-only and ignored if sent.
- A quiz of another user returns `403`, an unknown id `404`.
- Logout without a `refresh_token` cookie or with an invalid one returns `401`.
- Questions contain `created_at`/`updated_at` only in the response of `POST /api/quizzes/`, as in the API doc.

## Troubleshooting

- **`HTTP Error 403: Forbidden` while creating a quiz** (visible in the `runserver` output): YouTube rejected the
  download. Clear the yt-dlp cache and try again:

  ```bash
  python -m yt_dlp --rm-cache-dir
  ```

  If it still fails, update yt-dlp with `pip install -U yt-dlp`.

- **`503 UNAVAILABLE` from Gemini**: the model is busy. Try again later or set another Flash model in
  `core/settings.py` (`GEMINI_MODEL`).
