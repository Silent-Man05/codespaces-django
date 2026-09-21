from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Image, ImageReaction, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    ordering = ["email"]
    list_display = ["email", "role", "is_active", "is_staff", "created_at"]
    search_fields = ["email"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Permissions", {"fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2", "role", "is_staff", "is_active")}),
    )
    readonly_fields = ["created_at", "updated_at", "last_login"]


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ["title", "uploaded_by", "uploaded_at", "views_count", "likes_count", "dislikes_count"]
    search_fields = ["title", "description", "uploaded_by__email"]


@admin.register(ImageReaction)
class ImageReactionAdmin(admin.ModelAdmin):
    list_display = ["image", "user", "reaction_type", "created_at"]
    list_filter = ["reaction_type"]
