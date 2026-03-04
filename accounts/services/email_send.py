# accounts/services/emailer.py
from __future__ import annotations

from django.conf import settings
from django.core.mail import send_mail


def send_claim_link_email(*, to_email: str, claim_url: str, purpose_label: str) -> None:
    """
    Sends a claim link email (invite/redeem).
    The actual delivery backend is configured in settings (SendGrid via Anymail).
    """
    subject = f"EELAP: Complete your account setup ({purpose_label})"
    body = (
        "Hello,\n\n"
        "Use the secure link below to complete your account setup. "
        "This link expires soon and can be used only once:\n\n"
        f"{claim_url}\n\n"
        "If you did not request this, you can ignore this email.\n\n"
        "— EELAP"
    )

    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        fail_silently=False,
    )