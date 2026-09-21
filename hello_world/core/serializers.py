from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import Image, ImageReaction, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "role", "is_active", "created_at", "updated_at"]
        read_only_fields = fields


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["email", "password"]

    def validate_email(self, value):
        return value.strip().lower()

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            is_active=False,
            role=User.Role.GUEST,
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            username=attrs["email"].strip().lower(),
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError("Invalid credentials or email not verified.")
        attrs["user"] = user
        return attrs


class RoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=User.Role.choices)


class ImageSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)

    class Meta:
        model = Image
        fields = [
            "id",
            "title",
            "description",
            "file",
            "uploaded_by",
            "uploaded_at",
            "views_count",
            "likes_count",
            "dislikes_count",
        ]
        read_only_fields = [
            "id",
            "uploaded_by",
            "uploaded_at",
            "views_count",
            "likes_count",
            "dislikes_count",
        ]


class ImageReactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ImageReaction
        fields = ["id", "image", "user", "reaction_type", "created_at"]
        read_only_fields = ["id", "image", "user", "created_at"]
