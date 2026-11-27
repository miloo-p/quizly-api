from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

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


class CookieTokenObtainPairView(TokenObtainPairView):
    """Logs a user in and sets the JWT tokens as HttpOnly cookies."""
    def post(self, request, *args, **kwargs):
        """Validates the credentials, returns the user and sets access and refresh cookie."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        response = Response(
            {
                "detail": "Login successfully!",
                "user": {
                    "id": serializer.user.id,
                    "username": serializer.user.username,
                    "email": serializer.user.email,
                },
            }
        )

        refresh = serializer.validated_data.get("refresh")
        access = serializer.validated_data.get("access")

        response.set_cookie(
            key="access_token",
            value=access,
            httponly=True,
            secure=True,
            samesite="Lax",
        )

        response.set_cookie(
            key="refresh_token",
            value=refresh,
            httponly=True,
            secure=True,
            samesite="Lax",
        )

        return response


class CookieTokenRefreshView(TokenRefreshView):
    """Issues a new access token from the refresh_token cookie."""
    def post(self, request, *args, **kwargs):
        """Reads the refresh cookie and sets a new access_token cookie."""
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token is None:
            return Response(
                {"detail": "Refresh token is not found!"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = self.get_serializer(data={"refresh": refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            return Response(
                {"detail": "Refresh token is invalid!"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        access_token = serializer.validated_data.get("access")

        response = Response({"detail": "Token refreshed"})

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="Lax",
        )

        return response


class LogoutView(APIView):
    """Logs the user out and invalidates the refresh token."""
    def post(self, request):
        """Blacklists the refresh token and deletes both token cookies."""
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token is None:
            return Response(
                {"detail": "Refresh token is not found!"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            return Response(
                {"detail": "Refresh token is invalid!"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        response = Response(
            {
                "detail": "Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid."
            }
        )
        response.delete_cookie("refresh_token")
        response.delete_cookie("access_token")
        return response
