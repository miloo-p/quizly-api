from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..utils import create_quiz_data, save_quiz
from .serializers import QuizCreateSerializer, QuizSerializer


class QuizListCreateView(APIView):
    def post(self, request):
        serializer = QuizCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        url = serializer.validated_data["url"]
        try:
            quiz_data = create_quiz_data(url)
        except Exception:
            return Response(
                {"detail": "Quiz could not be created from this video."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        quiz = save_quiz(request.user, url, quiz_data)
        return Response(QuizSerializer(quiz).data, status=status.HTTP_201_CREATED)
