# the logic for account claiming (OTP generation, validation, etc.) goes here
# accounts/services/claims.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.core import signing

from accounts.models import (
    AccountClaim,
    ClaimPurpose,
    User,
    UserRole,
    StudentProfile,
    LecturerProfile,
    RosterEntry,
    RosterStatus,
)

from .token_encryption import make_claim_token, read_claim_token
from .email_send import send_claim_link_email


CLAIM_EXPIRY_MINUTES = 20
CLAIM_TOKEN_MAX_AGE_SECONDS = CLAIM_EXPIRY_MINUTES * 60


@dataclass(frozen=True)
class ClaimStartResult:
    claim_id: str
    expires_in_seconds: int
    claim_url: str


def _expires_at():
    return timezone.now() + timedelta(minutes=CLAIM_EXPIRY_MINUTES)


def _build_claim_url(frontend_base_url: str, token: str) -> str:
    # You can standardize your frontend route here:
    # e.g. https://app.example.com/claim?token=...
    base = frontend_base_url.rstrip("/")
    return f"{base}/claim?token={token}"


@transaction.atomic
def start_student_claim(*, email: str, frontend_base_url: str, send_email: bool = True) -> ClaimStartResult:
    # Find email in LOCKED roster (latest version first)
    entry = (
        RosterEntry.objects.select_related("roster")
        .filter(email__iexact=email.strip(), is_removed=False, roster__status=RosterStatus.LOCKED)
        .order_by("-roster__version")
        .first()
    )
    if not entry:
        # In production consider returning a generic response to avoid email enumeration.
        raise ValueError("Email not found in locked roster")

    # If student already activated, you can stop early
    existing_user = User.objects.filter(email__iexact=entry.email.strip()).first()
    if existing_user and existing_user.is_active:
        raise ValueError("Account already active")

    claim = AccountClaim.objects.create(
        email=entry.email.strip().lower(),
        purpose=ClaimPurpose.STUDENT_REDEEM,
        role_to_assign=UserRole.STUDENT,
        roster_entry=entry,
        expires_at=_expires_at(),
        otp_hash=None,  # legacy field if still present
    )

    token = make_claim_token(claim_id=str(claim.id))
    claim_url = _build_claim_url(frontend_base_url, token)

    if send_email:
        send_claim_link_email(
            to_email=claim.email,
            claim_url=claim_url,
            purpose_label="Student Redemption",
        )

    return ClaimStartResult(claim_id=str(claim.id), expires_in_seconds=CLAIM_TOKEN_MAX_AGE_SECONDS, claim_url=claim_url)


@transaction.atomic
def start_lecturer_claim(*, email: str, frontend_base_url: str, send_email: bool = True) -> ClaimStartResult:
    # Lecturer claim must be pre-created by SUPERADMIN invite endpoint
    claim = (
        AccountClaim.objects.filter(
            email__iexact=email.strip(),
            purpose=ClaimPurpose.LECTURER_INVITE,
            is_used=False,
        )
        .order_by("-created_at")
        .first()
    )
    if not claim:
        raise ValueError("No pending lecturer invite for this email")

    # refresh expiry on resend
    claim.expires_at = _expires_at()
    claim.save(update_fields=["expires_at"])

    token = make_claim_token(claim_id=str(claim.id))
    claim_url = _build_claim_url(frontend_base_url, token)

    if send_email:
        send_claim_link_email(
            to_email=claim.email,
            claim_url=claim_url,
            purpose_label="Lecturer Invitation",
        )

    return ClaimStartResult(claim_id=str(claim.id), expires_in_seconds=CLAIM_TOKEN_MAX_AGE_SECONDS, claim_url=claim_url)


def _get_valid_claim_from_token(token: str) -> AccountClaim:
    claim_id = read_claim_token(token, max_age_seconds=CLAIM_TOKEN_MAX_AGE_SECONDS)

    claim = AccountClaim.objects.select_related("roster_entry").get(id=claim_id)

    if claim.is_used:
        raise ValueError("Claim already used")

    if timezone.now() >= claim.expires_at:
        # Even if token hasn't expired (clock skew), DB is the source-of-truth too.
        raise signing.SignatureExpired("Claim expired")

    return claim


@transaction.atomic
def complete_claim(*, token: str, password: str) -> User:
    claim = _get_valid_claim_from_token(token)

    email = claim.email.strip().lower()

    user, _created = User.objects.get_or_create(
        email=email,
        defaults={"role": claim.role_to_assign, "is_active": True},
    )

    # enforce role consistency
    if user.role != claim.role_to_assign:
        raise ValueError("Role mismatch for this claim")

    # set password + activate
    user.set_password(password)
    user.is_active = True
    user.save(update_fields=["password", "is_active"])

    # create profile
    if claim.role_to_assign == UserRole.STUDENT:
        if not claim.roster_entry:
            raise ValueError("Student claim missing roster entry")
        StudentProfile.objects.get_or_create(user=user, defaults={"roster_entry": claim.roster_entry})

    elif claim.role_to_assign == UserRole.LECTURER:
        LecturerProfile.objects.get_or_create(user=user)

    # mark used
    claim.mark_used()
    claim.save(update_fields=["is_used", "used_at"])

    return user