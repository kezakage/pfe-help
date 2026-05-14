from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Discipline, User, UserDiscipline


@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    list_display = ("name_fr", "name_ar", "color_hex")
    search_fields = ("name_fr", "name_ar")


class UserDisciplineInline(admin.TabularInline):
    model = UserDiscipline
    extra = 0


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("-created_at",)
    list_display = ("email", "first_name", "last_name", "role", "status", "is_active")
    list_filter = ("role", "status", "is_active", "is_staff")
    search_fields = ("email", "first_name", "last_name", "institution_name")
    inlines = (UserDisciplineInline,)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("first_name", "last_name", "institution_name", "bio")}),
        ("Role & Status", {"fields": ("role", "status", "validated_by", "validated_at")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined", "last_login_at")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "role", "status"),
        }),
    )
    readonly_fields = ("last_login", "date_joined")
