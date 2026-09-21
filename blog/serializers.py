# import 
import base64
import uuid
from io import BytesIO
from PIL import Image
# import imghdr

from django.core.files.base import ContentFile
from rest_framework import serializers,status
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


# from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from django.core.validators import RegexValidator
from .models import Image, ImageReaction
# from .models import Image to Image, ImageReaction to ImageReaction, 

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from django.core.validators import RegexValidator



User = get_user_model()

class Base64ImageField(serializers.ImageField):
    """
    Accepts base64-encoded images and converts them into Django ContentFile.
    """
    def to_internal_value(self, data):
        # If it's a base64 string
        if isinstance(data, str) and data.startswith('data:image'):
            # Format: data:image/png;base64,XXXX
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]  # e.g., png, jpg
            data = ContentFile(base64.b64decode(imgstr), name=f'{uuid.uuid4()}.{ext}')
        return super().to_internal_value(data)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value):
        validate_password(value)
        return value

class UserSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "role", "user_status",
            "first_name", "last_name",
            "address", "phone_number", "image", "password"
        ]
        extra_kwargs = {
            "password": {"write_only": True}
        }

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Extend JWT login response to include user role and status."""
    def validate(self, attrs):
        data = super().validate(attrs)
        data["role"] = self.user.role
        data["user_status"] = self.user.user_status
        return data



class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        required=True,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="This username is already taken."
            )
        ]
    )

    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="This email is already registered."
            )
        ]
    )

    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        validators=[validate_password],
    )

    phone_number = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        validators=[
            RegexValidator(
                regex=r"^\+?[0-9]{7,15}$",
                message="Enter a valid phone number."
            )
        ]
    )

    image = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "role",
            "address",
            "phone_number",
            "image",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
        }

    # Normalize email
    def validate_email(self, value):
        return value.lower()

    # Prevent admin registration
    def validate_role(self, value):
        if value == "admin":
            raise serializers.ValidationError(
                "Admin accounts cannot be registered via this endpoint."
            )
        return value

    # Extra password control
    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long."
            )
        return value

    def validate(self, attrs):
        if attrs.get("user_type") == "group_rep" and not attrs.get("officename"):
            raise serializers.ValidationError({
                "officename": "Office name is required for group representatives."
            })
        return attrs



    def create(self, validated_data):
        password = validated_data.pop("password")
        image_b64 = validated_data.pop("image", None)

        user = User(**validated_data)
        user.set_password(password)  # secure hashing

        # ✅ Handle Base64 image with Pillow
        if image_b64:
            if "base64," in image_b64:
                image_b64 = image_b64.split("base64,", 1)[1]

            image_data = base64.b64decode(image_b64)
            try:
                image = Image.open(BytesIO(image_data))
                ext = image.format.lower()  # e.g., 'png', 'jpeg'
            except Exception:
                ext = "png"  # fallback if format can't be detected

            file_name = f"{uuid.uuid4()}.{ext}"
            user.image.save(file_name, ContentFile(image_data), save=False)

        user.save()
        return user


class ImageReactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ImageReaction
        fields = ["id", "image", "reaction", "user"]
        read_only_fields = ["id", "user"]

    def create(self, validated_data):
        user = self.context["request"].user
        image = validated_data["image"]
        reaction_value = validated_data["reaction"]

        reaction, created = ImageReaction.objects.update_or_create(
            user=user,
            image=image,
            defaults={"reaction": reaction_value}
        )

        return reaction



        # ImageSerializer to ImageSerializer 

class ImageSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    reactions = ImageReactionSerializer(many=True, read_only=True)
    # images = serializers.ImageField(required=False, allow_null=True)
    images = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Image
        fields = [
            "id",
            "title",
            "description",
            "images",
            "created_by",
            "created_at",
            "updated_at",
            "reactions",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        user = self.context["request"].user
        return Image.objects.create(created_by=user, **validated_data)


