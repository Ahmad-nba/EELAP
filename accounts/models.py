# accounts/models.py
from __future__ import annotations
from datetime import datetime, timedelta

import uuid
from datetime import timedelta
from typing import ClassVar

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from accounts.managers import UserManager


class UserRole(models.TextChoices):
    SUPERADMIN = "SUPERADMIN", "Super Admin"
    LECTURER = "LECTURER", "Lecturer"
    STUDENT = "STUDENT", "Student"


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    username = None  # REMOVE username field
    email = models.EmailField(unique=True)

    role = models.CharField(max_length=16, choices=UserRole.choices, default=UserRole.STUDENT)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects: ClassVar[UserManager] = UserManager()

    def __str__(self) -> str:
        return f"{self.email} ({self.role})"

class LecturerProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lecturer_profile",
    )

    department = models.CharField(max_length=120, blank=True)
    staff_id = models.CharField(max_length=64, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"LecturerProfile<{self.id}>"


class StudentProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )

    # Critical link: student account <-> locked roster truth
    roster_entry = models.OneToOneField(
        "RosterEntry",
        on_delete=models.PROTECT,
        related_name="student_profile",
        help_text="The locked roster row this student account is bound to.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"StudentProfile<{self.user.email}>"


class LabSeries(models.Model):
    """
    Configuration-domain object:
    A lab series belongs to exactly one lecturer (owner).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_labseries",
        help_text="The lecturer who owns/manages this lab series.",
    )

    title = models.CharField(max_length=200)
    code = models.CharField(max_length=64, blank=True)  # optional (e.g., ELE1202-LAB)
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(2000)], default=timezone.now().year
    )
    semester = models.CharField(
        max_length=32, blank=True
    )  # keep string flexible (e.g., 'Sem 1')

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["owner"]),
            models.Index(fields=["code"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.year} {self.semester})"


class RosterStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    LOCKED = "LOCKED", "Locked"


class Roster(models.Model):
    """
    A roster belongs to a lab series.
    LOCKED rosters are the source of truth for account redemption and attendance expectation.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    lab_series = models.ForeignKey(
        LabSeries, on_delete=models.CASCADE, related_name="rosters"
    )

    status = models.CharField(
        max_length=16, choices=RosterStatus.choices, default=RosterStatus.DRAFT
    )

    version = models.PositiveIntegerField(default=1)
    locked_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="locked_rosters",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["lab_series", "status"]),
            models.Index(fields=["lab_series", "version"]),
        ]
        constraints = [
            # Optional: enforce one active DRAFT roster per lab series
            models.UniqueConstraint(
                fields=["lab_series", "status"],
                condition=models.Q(status=RosterStatus.DRAFT),
                name="uniq_draft_roster_per_lab_series",
            )
        ]

    def __str__(self) -> str:
        return f"Roster<v{self.version} [{self.status}]> for {self.lab_series}"


class Group(models.Model):
    """
    Groups like comp1, comp2, bio1 etc. belong to a roster.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    roster = models.ForeignKey(Roster, on_delete=models.CASCADE, related_name="groups")
    label = models.CharField(max_length=64)
    capacity = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["roster", "label"])]
        constraints = [
            models.UniqueConstraint(
                fields=["roster", "label"], name="uniq_group_label_per_roster"
            )
        ]

    def __str__(self) -> str:
        return f"Group<{self.label}> (Roster {self.roster})"


class RosterEntry(models.Model):
    """
    A single student row in a roster.
    Email is the key used for redemption.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    roster = models.ForeignKey(Roster, on_delete=models.CASCADE, related_name="entries")
    group = models.ForeignKey(Group, on_delete=models.PROTECT, related_name="entries")

    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    reg_no = models.CharField(max_length=64, blank=True)
    program = models.CharField(max_length=120, blank=True)
    gender = models.CharField(max_length=32, blank=True)

    is_removed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["roster", "email"]),
        ]
        constraints = [
            # A given email should not appear twice in the same roster version.
            models.UniqueConstraint(
                fields=["roster", "email"], name="uniq_email_per_roster"
            ),
        ]

    def __str__(self) -> str:
        return f"RosterEntry<{self.email}> (Roster {self.roster})"


class ClaimPurpose(models.TextChoices):
    LECTURER_INVITE = "LECTURER_INVITE", "Lecturer Invite"
    STUDENT_REDEEM = "STUDENT_REDEEM", "Student Redeem"


class AccountClaim(models.Model):
    """
    Shared OTP claim system for:
    - Lecturer invitation claim
    - Student account redemption claim

    Store only otp_hash (never OTP plaintext).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField()
    purpose = models.CharField(max_length=32, choices=ClaimPurpose.choices)

    role_to_assign = models.CharField(max_length=16, choices=UserRole.choices)

    # Student redeem ties to roster entry; lecturer invite ties to invited_by.
    roster_entry = models.ForeignKey(
        RosterEntry,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="claims",
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="sent_claims",
    )

    #: otp_hash = models.CharField(max_length=128) token style
    otp_hash = models.CharField(max_length=128, blank=True, null=True)  # temporary legacy field
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    attempt_count = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)

    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["email", "purpose"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["is_used"]),
        ]

    @classmethod
    def default_expiry(cls) -> datetime:
        return timezone.now() + timedelta(minutes=20)

    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    def mark_used(self) -> None:
        self.is_used = True
        self.used_at = timezone.now()

    def __str__(self) -> str:
        return f"AccountClaim<{self.email}> {self.purpose} used={self.is_used}"
