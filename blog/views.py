
from rest_framework import generics, viewsets, permissions
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser,JSONParser
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_yasg.utils import swagger_auto_schema
from django.db.models import Q

from .serializers import (
    RegisterSerializer,
    ImageSerializer,
    ImageReactionSerializer,
    UserSerializer,
    CustomTokenObtainPairSerializer,
    ChangePasswordSerializer,
)
from .models import Image, ImageReaction
from .permissions import IsAdminUserRole, IsAdminOrGuest, IsAdminOrSelf

#  lwa kuchange password
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.password_validation import validate_password
from django.shortcuts import render

User = get_user_model()


def landing_page(request):
    return render(request, "landing.html")


class ValidateUserFieldView(APIView):
    permission_classes = []  # allow public access

    def get(self, request):
        username = request.query_params.get("username")
        email = request.query_params.get("email")

        data = {}

        if username is not None:
            data["username_available"] = not User.objects.filter(
                username__iexact=username
            ).exists()

        if email is not None:
            data["email_available"] = not User.objects.filter(
                email__iexact=email
            ).exists()

        if not data:
            return Response(
                {"detail": "Provide username or email to validate."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(data, status=status.HTTP_200_OK)


class MeView(generics.RetrieveUpdateAPIView):
    """
    Endpoint for the currently authenticated user to view/update their own details.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
    


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=ChangePasswordSerializer)
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()

        return Response({"detail": "Password updated successfully"})

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSelf]

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()
        if not user.is_authenticated:
            return User.objects.none()
        if user.role == "admin":
            return User.objects.all()
        return User.objects.filter(id=user.id)



class RegisterView(generics.CreateAPIView):
    """
    Registration view for customers only.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    @swagger_auto_schema(request_body=CustomTokenObtainPairSerializer)
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    parser_classes = [MultiPartParser, FormParser,JSONParser]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminUserRole()]
        return [IsAdminOrGuest()]
    # ❌ perform_create no longer needed, serializer handles created_by automatically


class ImageReactionViewSet(viewsets.ModelViewSet):
    queryset = ImageReaction.objects.all()
    serializer_class = ImageReactionSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "list", "retrieve"]:
            return [IsAdminOrGuest()]
        return [IsAdminUserRole()]







