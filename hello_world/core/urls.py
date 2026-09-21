from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    ImageDetailView,
    ImageListCreateView,
    ImageReactionView,
    LoginView,
    RoleManagementView,
    SignupView,
    VerifyEmailView,
)

app_name = "api"

urlpatterns = [
    path("auth/signup/", SignupView.as_view(), name="signup"),
    path("auth/verify/", VerifyEmailView.as_view(), name="verify-email"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/users/<int:user_id>/role/", RoleManagementView.as_view(), name="role-management"),
    path("images/", ImageListCreateView.as_view(), name="image-list-create"),
    path("images/<int:pk>/", ImageDetailView.as_view(), name="image-detail"),
    path("images/<int:image_id>/reactions/", ImageReactionView.as_view(), name="image-reactions"),
]
