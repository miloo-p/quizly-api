from django.contrib import admin

from .models import Question, Quiz


class QuestionInline(admin.TabularInline):
    """Shows and edits the questions directly on the quiz page."""
    model = Question
    extra = 0


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Admin for quizzes with their questions as inline."""
    list_display = ["title", "user", "created_at"]
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin for editing single questions."""
    list_display = ["question_title", "quiz"]
