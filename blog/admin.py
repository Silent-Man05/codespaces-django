


from django.contrib import admin
from .models import User, Image, ImageReaction


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id", "username", "email", "role", "user_status",
        "first_name", "last_name", "phone_number"
    )
    list_filter = ("role", "user_status", "is_staff", "is_superuser")
    search_fields = ("username", "email", "first_name", "last_name", "phone_number")
    ordering = ("id",)
    readonly_fields = ("last_login", "date_joined")


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ("id", "title",  "description", "created_by", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("title", "description", "created_by__username")
    ordering = ("-created_at",)


@admin.register(ImageReaction)
class ImageReactionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "image", "reaction")
    list_filter = ("reaction",)
    search_fields = ("user__username", "image__title")


