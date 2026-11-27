from rest_framework.permissions import BasePermission


class IsCreatorOfQuiz(BasePermission):
    """Allows access to a quiz only for the user who created it."""
    def has_object_permission(self, request, view, obj):
        """Returns True if the quiz belongs to the requesting user."""
        return obj.user == request.user
