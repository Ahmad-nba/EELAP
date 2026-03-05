# accounts/serializers.py
from __future__ import annotations

from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class StudentClaimStartSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ClaimCompleteSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(min_length=8, write_only=True)


class LecturerInviteSerializer(serializers.Serializer):
    email = serializers.EmailField()


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Uses User.USERNAME_FIELD which is 'email' in our custom user model.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = getattr(user, "role", "")
        token["email"] = getattr(user, "email", "")
        return token

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if not email or not password:
            raise serializers.ValidationError("Both email and password are required.")

        request = self.context.get("request")

        # Key fix: authenticate using email (since USERNAME_FIELD = 'email')
        user = authenticate(request=request, email=email, password=password)

        # Fallback (some setups still expect username kwarg)
        if user is None:
            user = authenticate(request=request, username=email, password=password)

        if user is None:
            raise serializers.ValidationError({"detail": "Invalid credentials."})

        attrs["user"] = user
        return attrs

