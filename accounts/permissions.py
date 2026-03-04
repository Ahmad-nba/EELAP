# accounts/permissions.py
from rest_framework.permissions import BasePermission

from accounts.models import UserRole


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (getattr(user, "role", None) == UserRole.SUPERADMIN )
        )