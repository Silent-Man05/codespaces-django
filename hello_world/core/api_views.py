from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Image, ImageReaction, User
from .permissions import IsActiveUser, IsAdminRole
from .serializers import (
    ImageReactionSerializer,
    ImageSerializer,
    LoginSerializer,
    RoleSerializer,
    SignupSerializer,
    UserSerializer,
)


def success(message, data=None, http_status=status.HTTP_200_OK):
    return Response(
        {"status": "success", "message": message, "data": data or {}},
        status=http_status,
    )


def token_response(user):
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": UserSerializer(user).data,
    }


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = user.issue_verification_token()
        verification_url = f"{settings.EMAIL_VERIFICATION_URL}?token={token}"
        send_mail(
            subject="Verify your PhotoLab account",
            message=(
                "Please verify your email address by opening this link:\n\n"
                f"{verification_url}"
            ),
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[user.email],
            fail_silently=False,
        )
        return success(
            "User registered successfully. Please verify your email.",
            {"user_id": user.id},
            status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        token = request.query_params.get("token", "")
        if not token:
            return Response(
                {"status": "error", "message": "Verification token is required.", "data": {}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token_hash = User.objects.exclude(verification_token_hash="")
        user = next(
            (candidate for candidate in token_hash if candidate.verify_token(token)),
            None,
        )
        if user is None:
            return Response(
                {"status": "error", "message": "Invalid or expired verification token.", "data": {}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_active = True
        user.verification_token_hash = ""
        user.save(update_fields=["is_active", "verification_token_hash", "updated_at"])
        return success("Email verified successfully. You can now log in.")


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return success("Login successful.", token_response(serializer.validated_data["user"]))


class ImageListCreateView(generics.ListCreateAPIView):
    queryset = Image.objects.select_related("uploaded_by").all()
    serializer_class = ImageSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    permission_classes = [IsActiveUser]

    def create(self, request, *args, **kwargs):
        if request.user.role != User.Role.ADMIN:
            return Response(
                {"status": "error", "message": "Admin role required.", "data": {}},
                status=status.HTTP_403_FORBIDDEN,
            )
        response = super().create(request, *args, **kwargs)
        return success("Image uploaded successfully.", response.data, response.status_code)

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return success("Images retrieved successfully.", response.data)


class ImageDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Image.objects.select_related("uploaded_by").all()
    serializer_class = ImageSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    permission_classes = [IsActiveUser]

    def _admin_only(self):
        return self.request.user.role == User.Role.ADMIN

    def retrieve(self, request, *args, **kwargs):
        image = self.get_object()
        Image.objects.filter(pk=image.pk).update(views_count=image.views_count + 1)
        image.views_count += 1
        return success("Image retrieved successfully.", self.get_serializer(image).data)

    def update(self, request, *args, **kwargs):
        if not self._admin_only():
            return Response(
                {"status": "error", "message": "Admin role required.", "data": {}},
                status=status.HTTP_403_FORBIDDEN,
            )
        response = super().update(request, *args, **kwargs)
        return success("Image updated successfully.", response.data)

    def destroy(self, request, *args, **kwargs):
        if not self._admin_only():
            return Response(
                {"status": "error", "message": "Admin role required.", "data": {}},
                status=status.HTTP_403_FORBIDDEN,
            )
        self.perform_destroy(self.get_object())
        return success("Image deleted successfully.")


class ImageReactionView(APIView):
    permission_classes = [IsActiveUser]

    def _image(self, image_id):
        return get_object_or_404(Image, pk=image_id)

    def _save_reaction(self, request, image_id, update=False):
        serializer = ImageReactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            image = get_object_or_404(Image.objects.select_for_update(), pk=image_id)
            reaction, created = ImageReaction.objects.update_or_create(
                image=image,
                user=request.user,
                defaults={"reaction_type": serializer.validated_data["reaction_type"]},
            )
            counts = ImageReaction.objects.filter(image=image).aggregate(
                likes=Count("id", filter=Q(reaction_type=ImageReaction.ReactionType.LIKE)),
                dislikes=Count("id", filter=Q(reaction_type=ImageReaction.ReactionType.DISLIKE)),
            )
            image.likes_count = counts["likes"] or 0
            image.dislikes_count = counts["dislikes"] or 0
            image.save(update_fields=["likes_count", "dislikes_count"])
        message = "Reaction updated successfully." if not created else "Reaction added successfully."
        return success(message, ImageReactionSerializer(reaction).data, status.HTTP_200_OK)

    def post(self, request, image_id):
        return self._save_reaction(request, image_id)

    def put(self, request, image_id):
        return self._save_reaction(request, image_id, update=True)

    def delete(self, request, image_id):
        with transaction.atomic():
            image = Image.objects.select_for_update().get(pk=image_id)
            reaction = get_object_or_404(ImageReaction, image=image, user=request.user)
            reaction.delete()
            counts = ImageReaction.objects.filter(image=image).aggregate(
                likes=Count("id", filter=Q(reaction_type=ImageReaction.ReactionType.LIKE)),
                dislikes=Count("id", filter=Q(reaction_type=ImageReaction.ReactionType.DISLIKE)),
            )
            image.likes_count = counts["likes"] or 0
            image.dislikes_count = counts["dislikes"] or 0
            image.save(update_fields=["likes_count", "dislikes_count"])
        return success("Reaction removed successfully.")


class RoleManagementView(APIView):
    permission_classes = [IsAdminRole]

    def patch(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        serializer = RoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.role = serializer.validated_data["role"]
        user.save(update_fields=["role", "updated_at"])
        return success("User role updated successfully.", UserSerializer(user).data)
