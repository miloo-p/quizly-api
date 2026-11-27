import json
import os
import tempfile
from urllib.parse import parse_qs, urlparse

import whisper
import yt_dlp
from django.conf import settings
from django.db import transaction
from google import genai

from .models import Question, Quiz

YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com"}

QUIZ_PROMPT = """
Create a quiz based on the following transcript.
Return ONLY valid JSON in exactly this structure:
{{
  "title": "short quiz title",
  "description": "one-sentence summary of the video",
  "questions": [
    {{
      "question_title": "the question",
      "question_options": ["option A", "option B", "option C", "option D"],
      "answer": "the correct option, exactly as written in question_options"
    }}
  ]
}}
Requirements: exactly 10 questions, exactly 4 distinct options each,
exactly one correct answer per question.

Transcript:
{transcript}
"""


def is_valid_youtube_url(url):
    """Returns True for youtube.com/watch URLs that contain a video id."""
    parsed = urlparse(url)
    has_video_id = bool(parse_qs(parsed.query).get("v"))
    return parsed.netloc in YOUTUBE_HOSTS and parsed.path == "/watch" and has_video_id


def parse_quiz_response(text):
    """Parses the Gemini JSON answer and checks it has exactly 10 questions."""
    quiz = json.loads(text)
    if len(quiz.get("questions", [])) != 10:
        raise ValueError("Quiz must contain exactly 10 questions.")
    return quiz


def download_audio(url, folder):
    """Downloads the audio track of the video into folder and returns the file path."""
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(folder, "audio.%(ext)s"),
        "quiet": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)


def transcribe_audio(audio_path):
    """Transcribes the audio file locally with Whisper and returns the text."""
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, fp16=False)
    return result["text"]


def generate_quiz(transcript):
    """Asks Gemini for a quiz based on the transcript and returns it as dict."""
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=QUIZ_PROMPT.format(transcript=transcript),
        config={"response_mime_type": "application/json"},
    )
    return parse_quiz_response(response.text)


def create_quiz_data(url):
    """Runs download, transcription and quiz generation; the audio is deleted afterwards."""
    with tempfile.TemporaryDirectory() as folder:
        audio_path = download_audio(url, folder)
        transcript = transcribe_audio(audio_path)
    return generate_quiz(transcript)


def save_quiz(user, url, quiz_data):
    """Saves the quiz with all questions in one transaction and returns the quiz."""
    with transaction.atomic():
        quiz = Quiz.objects.create(
            user=user,
            title=quiz_data["title"],
            description=quiz_data["description"],
            video_url=url,
        )
        for question in quiz_data["questions"]:
            Question.objects.create(
                quiz=quiz,
                question_title=question["question_title"],
                question_options=question["question_options"],
                answer=question["answer"],
            )
    return quiz
