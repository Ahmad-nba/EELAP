# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (
    User,
    LecturerProfile,
    StudentProfile,
    LabSeries,
    Roster,
    Group,
    RosterEntry,
    AccountClaim,
)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User

    list_display = ("email", "role", "is_active", "is_staff", "is_superuser")
    list_filter = ("role", "is_active", "is_staff", "is_superuser")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)

    # Since username is removed, adjust admin forms
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Permissions", {"fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2", "role")}),
    )


admin.site.register(LecturerProfile)
admin.site.register(StudentProfile)
admin.site.register(LabSeries)
admin.site.register(Roster)
admin.site.register(Group)
admin.site.register(RosterEntry)
admin.site.register(AccountClaim)