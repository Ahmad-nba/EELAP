# accounts/services/invites.py
from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from accounts.models import AccountClaim, ClaimPurpose, User, UserRole
from .account_claim import start_lecturer_claim


@transaction.atomic
def invite_lecturer(*, email: str, invited_by: User, frontend_base_url: str) -> dict:
    """
    Creates (or reuses) a lecturer placeholder user + creates an invite claim,
    then emails the link using start_lecturer_claim().
    """
    normalized_email = email.strip().lower()

    # Create placeholder user if missing
    user, _created = User.objects.get_or_create(
        email=normalized_email,
        defaults={"role": UserRole.LECTURER, "is_active": False},
    )

    # If the user exists but is not lecturer, that's a conflict
    if user.role != UserRole.LECTURER:
        raise ValueError("Email belongs to a non-lecturer account")

    # If already active, don't invite again
    if user.is_active:
        raise ValueError("Lecturer account is already active")

    # Create a new invite claim (or you could reuse the latest unused one)
    AccountClaim.objects.create(
        email=normalized_email,
        purpose=ClaimPurpose.LECTURER_INVITE,
        role_to_assign=UserRole.LECTURER,
        invited_by=invited_by,
        expires_at=timezone.now(),  # will be refreshed by start_lecturer_claim
        otp_hash=None,  # legacy field if still present
    )

    # This refreshes expiry + sends email link
    result = start_lecturer_claim(email=normalized_email, frontend_base_url=frontend_base_url, send_email=True)

    return {
        "claim_id": result.claim_id,
        "expires_in_seconds": result.expires_in_seconds,
        "claim_url": result.claim_url,  # useful in dev; hide in prod if you want
    }