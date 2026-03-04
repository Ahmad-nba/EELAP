# gives us a signed token 
# accounts/services/tokens.py
from __future__ import annotations

from typing import Any

from django.core import signing


CLAIM_TOKEN_SALT = "eelap.accounts.claim"


def make_claim_token(*, claim_id: str) -> str:
    """
    Signed token safe for URLs.
    Payload is minimal: claim_id only.
    """
    payload: dict[str, Any] = {"claim_id": claim_id}
    return signing.dumps(payload, salt=CLAIM_TOKEN_SALT)


def read_claim_token(token: str, *, max_age_seconds: int) -> str:
    """
    Verify signature + expiry and return claim_id.
    Raises signing.BadSignature / signing.SignatureExpired on failure.
    """
    data = signing.loads(token, salt=CLAIM_TOKEN_SALT, max_age=max_age_seconds)
    if not isinstance(data, dict) or "claim_id" not in data:
        raise signing.BadSignature("Invalid claim token payload")
    return str(data["claim_id"])