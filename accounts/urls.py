# accounts/urls.py
from django.urls import path

from accounts.views import (
    StudentClaimStartView,
    ClaimCompleteView,
    LecturerInviteView,
)

urlpatterns = [
    # Student redemption
    path("claim/student/start/", StudentClaimStartView.as_view(), name="student-claim-start"),

    # Complete (students + lecturers)
    path("claim/complete/", ClaimCompleteView.as_view(), name="claim-complete"),

    # Superadmin lecturer invite
    path("lecturers/invite/", LecturerInviteView.as_view(), name="lecturer-invite"),
]