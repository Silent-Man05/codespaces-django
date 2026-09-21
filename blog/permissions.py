# from rest_framework.permissions import BasePermission
from rest_framework.permissions import BasePermission, SAFE_METHODS
class IsAdminUserRole(BasePermission):
    """Allow access only to users with role=admin"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, "role", None) == "admin"


class IsGuestUserRole(BasePermission):
    """Allow access only to users with role=guest"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, "role", None) == "guest"


class IsAdminOrGuest(BasePermission):
    """Allow access to users with role=admin OR role=guest"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, "role", None) in ["admin", "guest"]

class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            getattr(request.user, "role", None) == "admin"
            or getattr(obj, "user", None) == request.user
        )





class IsAdminOrSelf(BasePermission):
    """
    Admins can do anything.
    Customers can only view or update their own data.
    For messages, customers can only access messages they sent or received.
    """

    def has_object_permission(self, request, view, obj):
        # Admins: full access
        if hasattr(request.user, "role") and request.user.role == "admin":
            return True

        # Customers: restrict to their own user object or messages
        if hasattr(request.user, "role") and request.user.role == "guest":
            # If object is a User → allow only self
            if obj == request.user and request.method in SAFE_METHODS + ("PUT", "PATCH"):
                return True

            # If object is a Message → allow if sender or recipient is self
            if hasattr(obj, "sender") and hasattr(obj, "recipient"):
                return obj.sender == request.user or obj.recipient == request.user

        return False

