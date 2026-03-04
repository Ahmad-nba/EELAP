from __future__ import annotations

from datetime import timedelta

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from accounts.models import (
    AccountClaim,
    ClaimPurpose,
    LabSeries,
    Roster,
    RosterEntry,
    Group,
    User,
    UserRole,
    RosterStatus,
)


class UserModelTests(TestCase):
    def test_email_is_username_field(self):
        self.assertEqual(User.USERNAME_FIELD, "email")


def test_unique_email(self):
    User.objects.create_user(
        email="a@example.com", password="pass1234", role=UserRole.STUDENT
    )
    with self.assertRaises(IntegrityError):
        User.objects.create_user(
            email="a@example.com", password="pass1234", role=UserRole.STUDENT
        )


class ClaimTests(TestCase):
    def test_default_expiry_is_roughly_20_minutes(self):
        expiry = AccountClaim.default_expiry()
        now = timezone.now()
        self.assertTrue(
            now + timedelta(minutes=19) <= expiry <= now + timedelta(minutes=21)
        )

    def test_is_expired(self):
        c = AccountClaim(
            email="x@example.com",
            purpose=ClaimPurpose.STUDENT_REDEEM,
            role_to_assign=UserRole.STUDENT,
            otp_hash="hash",
            expires_at=timezone.now() - timedelta(seconds=1),
        )
        self.assertTrue(c.is_expired())


class RosterConstraintsTests(TestCase):
    def setUp(self):
        self.lecturer = User.objects.create_user(
            email="lect@example.com",
            password="pass1234",
            role=UserRole.LECTURER,
            is_active=True,
        )
        self.lab = LabSeries.objects.create(
            owner=self.lecturer,
            title="ELE Lab",
            code="ELE-LAB",
            year=2026,
            semester="1",
        )

    def test_only_one_draft_roster_per_lab_series(self):
        Roster.objects.create(lab_series=self.lab, status=RosterStatus.DRAFT, version=1)
        with self.assertRaises(IntegrityError):
            Roster.objects.create(
                lab_series=self.lab, status=RosterStatus.DRAFT, version=2
            )

    def test_unique_email_per_roster(self):
        roster = Roster.objects.create(
            lab_series=self.lab, status=RosterStatus.DRAFT, version=1
        )
        g = Group.objects.create(roster=roster, label="comp1", capacity=50)

        RosterEntry.objects.create(
            roster=roster,
            group=g,
            full_name="A One",
            email="stud@example.com",
        )
        with self.assertRaises(IntegrityError):
            RosterEntry.objects.create(
                roster=roster,
                group=g,
                full_name="B Two",
                email="stud@example.com",
            )
