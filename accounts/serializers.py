# accounts/serializers.py
from __future__ import annotations

from rest_framework import serializers


class StudentClaimStartSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ClaimCompleteSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(min_length=8, write_only=True)


class LecturerInviteSerializer(serializers.Serializer):
    email = serializers.EmailField()

    # Optional: you can include profile fields later
    # full_name = serializers.CharField(required=False, allow_blank=True)