from django.urls import path,include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static

from .views import (
    UserViewSet,
    ImageViewSet,
    ImageReactionViewSet,
    CustomTokenObtainPairView,
    RegisterView,
    MeView,
    ChangePasswordView,
    ValidateUserFieldView,
)

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("images", ImageViewSet, basename="image")
router.register("reactions", ImageReactionViewSet, basename="reaction")

urlpatterns = [
    # User registration & profile
    path("register/", RegisterView.as_view(), name="register"),
    path("validate/", ValidateUserFieldView.as_view(), name="validate_user"),
    
    path("api/me/", MeView.as_view(), name="me"),
     path("api/me/change-password/", ChangePasswordView.as_view(), name="change_password"),

    # JWT login & refresh
    path("api/token/", CustomTokenObtainPairView.as_view(), name="custom_token_obtain_pair"),
    # path("api/login/", CustomTokenObtainPairView.as_view(), name="custom_token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

# Include router-generated endpoints
urlpatterns += router.urls

# Serve media files in development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
