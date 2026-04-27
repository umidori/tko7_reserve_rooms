from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User

    list_display = (
        "id",
        "login_id",
        "name",
        "role",
        "department",
        "is_active",
        "last_login",
    )
    list_filter = ("role", "is_active", "department")
    search_fields = ("login_id", "name")
    ordering = ("id",)

    fieldsets = (
        (None, {"fields": ("login_id", "password")}),
        ("基本情報", {"fields": ("name", "department", "role")}),
        (
            "権限",
            {"fields": ("is_active", "is_superuser", "groups", "user_permissions")},
        ),
        ("日時", {"fields": ("last_login", "created_at", "updated_at")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "login_id",
                    "name",
                    "password1",
                    "password2",
                    "role",
                    "department",
                    "is_active",
                ),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at", "last_login")
