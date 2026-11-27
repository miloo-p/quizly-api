from rest_framework import serializers

from ..models import Question, Quiz
from ..utils import is_valid_youtube_url


class QuizCreateSerializer(serializers.Serializer):
    """Validates the YouTube URL sent to create a quiz."""
    url = serializers.URLField()

    def validate_url(self, value):
        """Rejects URLs that are not a youtube.com/watch link with a video id."""
        if not is_valid_youtube_url(value):
            raise serializers.ValidationError("Please enter a valid YouTube URL.")
        return value


class QuestionSerializer(serializers.ModelSerializer):
    """Question with timestamps, used in the response of quiz creation."""
    class Meta:
        model = Question
        fields = ["id", "question_title", "question_options", "answer", "created_at", "updated_at"]


class QuizSerializer(serializers.ModelSerializer):
    """Quiz with nested questions including timestamps."""
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = [
            "id",
            "title",
            "description",
            "created_at",
            "updated_at",
            "video_url",
            "questions",
        ]
        read_only_fields = ["video_url"]


class QuestionListSerializer(serializers.ModelSerializer):
    """Question without timestamps, used for reading and updating quizzes."""
    class Meta:
        model = Question
        fields = ["id", "question_title", "question_options", "answer"]


class QuizReadSerializer(QuizSerializer):
    """Quiz with nested questions without timestamps (list, detail, update)."""
    questions = QuestionListSerializer(many=True, read_only=True)
