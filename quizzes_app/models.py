from django.conf import settings
from django.db import models


class Quiz(models.Model):
    """
    Quiz related to a User.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quizzes"
    )
    title = models.TextField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    video_url = models.URLField()

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"

    def __str__(self):
        """
        Shows the title, e.g. in the admin.
        """
        return self.title


class Question(models.Model):
    """
    Question related to a Quiz.
    """

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    question_title = models.TextField()
    question_options = models.JSONField(default=list)
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "Question"
        verbose_name_plural = "Questions"

    def __str__(self):
        """
        Shows the question_title, e.g. in the admin.
        """
        return self.question_title
