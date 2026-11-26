from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Quiz
from ..utils import create_quiz_data, save_quiz
from .permissions import IsCreatorOfQuiz
from .serializers import QuizCreateSerializer, QuizReadSerializer, QuizSerializer


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

    def get(self, request):
        quizzes = Quiz.objects.filter(user=request.user)
        return Response(QuizReadSerializer(quizzes, many=True).data)


class QuizDetailView(APIView):
    permission_classes = [IsAuthenticated, IsCreatorOfQuiz]

    def get(self, request, pk):
        """
        Returns a single quiz.
        """
        quiz = get_object_or_404(Quiz, pk=pk)
        self.check_object_permissions(request, quiz)
        serializer = QuizReadSerializer(quiz)
        return Response(serializer.data)

    def delete(self, request, pk):
        """
        Deletes a single quiz.
        """
        quiz = get_object_or_404(Quiz, pk=pk)
        self.check_object_permissions(request, quiz)
        quiz.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, pk):
        """
        Updates quiz values (partial allowed).
        """
        quiz = get_object_or_404(Quiz, pk=pk)
        self.check_object_permissions(request, quiz)
        serializer = QuizSerializer(quiz, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
