from __future__ import annotations

from django.core import signing
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import EmailTokenObtainPairSerializer

from accounts.permissions import IsSuperAdmin
from accounts.serializers import (
    StudentClaimStartSerializer,
    ClaimCompleteSerializer,
    LecturerInviteSerializer,
    UserLoginSerializer,
)
from accounts.services.account_claim import start_student_claim, complete_claim
from accounts.services.invites import invite_lecturer


def _get_frontend_base_url(request) -> str:
    """
    For dev, you can pass this via settings or env.
    For now, we allow header override for flexibility:
      X-FRONTEND-BASE-URL: http://localhost:3000
    Fallback: http://localhost:3000
    """
    return request.headers.get("X-FRONTEND-BASE-URL", "http://localhost:3000")


class StudentClaimStartView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = StudentClaimStartSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        email = ser.validated_data["email"]
        frontend_base_url = _get_frontend_base_url(request)

        try:
            result = start_student_claim(
                email=email, frontend_base_url=frontend_base_url, send_email=True
            )
        except ValueError as e:
            # In production you may want generic response to avoid email enumeration.
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "detail": "Claim link sent if eligible.",
                "expires_in_seconds": result.expires_in_seconds,
                # For dev you may return claim_url to speed testing; remove in prod.
                "claim_url": result.claim_url,
            },
            status=status.HTTP_200_OK,
        )


class ClaimCompleteView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = ClaimCompleteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        token = ser.validated_data["token"]
        password = ser.validated_data["password"]

        try:
            user = complete_claim(token=token, password=password)
        except signing.SignatureExpired:
            return Response(
                {"detail": "Link expired. Please request a new one."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except signing.BadSignature:
            return Response(
                {"detail": "Invalid link token."}, status=status.HTTP_400_BAD_REQUEST
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "detail": "Account activated successfully.",
                "user": {"id": str(user.id), "email": user.email, "role": user.role},
            },
            status=status.HTTP_200_OK,
        )


class LecturerInviteView(APIView):
    """
    SUPERADMIN invites lecturer by email.
    Creates placeholder lecturer user + invite claim + sends link email.
    """

    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        ser = LecturerInviteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        email = ser.validated_data["email"]
        frontend_base_url = _get_frontend_base_url(request)

        try:
            data = invite_lecturer(
                email=email,
                invited_by=request.user,
                frontend_base_url=frontend_base_url,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "detail": "Lecturer invite sent.",
                "invite": data,  # contains claim_url for dev; remove in prod if you want
            },
            status=status.HTTP_201_CREATED,
        )


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


# login view using email + password, returns JWT access + refresh tokens
class LoginView(APIView):
    def post(self, request):
        serializer = UserLoginSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]  #
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "email": user.email,
                    "username": user.username,
                    "role": user.role,
                },
            },
            status=status.HTTP_200_OK,
        )
