from django.contrib.auth.models import User
from rest_framework import serializers


class RegistrationSerializer(serializers.ModelSerializer):
    """Validates registration data and creates a new user."""

    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "confirmed_password"]
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"required": True, "allow_blank": False},
        }

    def validate_confirmed_password(self, value):
        """Checks that both passwords match."""
        password = self.initial_data.get("password")
        if password and value and password != value:
            raise serializers.ValidationError("Passwords do not match")
        return value

    def validate_email(self, value):
        """Rejects an email that is already used by another user."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def save(self):
        """Creates the user with a hashed password."""
        pw = self.validated_data["password"]

        account = User(email=self.validated_data["email"], username=self.validated_data["username"])
        account.set_password(pw)
        account.save()
        return account
