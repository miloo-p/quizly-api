from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RegistrationSerializer


class RegistrationView(APIView):
    """Registers a new user."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Creates a user and returns the success message from the API doc."""
        serializer = RegistrationSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response(
                {"detail": "User created successfully!"}, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
