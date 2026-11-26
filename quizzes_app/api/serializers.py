from rest_framework import serializers

from ..models import Question, Quiz
from ..utils import is_valid_youtube_url


class QuizCreateSerializer(serializers.Serializer):
    url = serializers.URLField()

    def validate_url(self, value):
        if not is_valid_youtube_url(value):
            raise serializers.ValidationError("Please enter a valid YouTube URL.")
        return value


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "question_title", "question_options", "answer", "created_at", "updated_at"]


class QuizSerializer(serializers.ModelSerializer):
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


class QuestionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "question_title", "question_options", "answer"]


class QuizReadSerializer(QuizSerializer):
    questions = QuestionListSerializer(many=True, read_only=True)
