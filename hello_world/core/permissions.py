from rest_framework.permissions import BasePermission

from .models import User


class IsAdminRole(BasePermission):
    message = "Admin role required."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and request.user.role == User.Role.ADMIN
        )


class IsActiveUser(BasePermission):
    message = "A verified account is required."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
        )
