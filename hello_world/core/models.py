import hashlib
import secrets

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        GUEST = "guest", "Guest"

    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.GUEST)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verification_token_hash = models.CharField(max_length=64, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    @property
    def username(self):
        return self.email

    def issue_verification_token(self):
        token = secrets.token_urlsafe(32)
        self.verification_token_hash = hashlib.sha256(token.encode()).hexdigest()
        self.save(update_fields=["verification_token_hash", "updated_at"])
        return token

    def verify_token(self, token):
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return secrets.compare_digest(self.verification_token_hash, token_hash)

    def __str__(self):
        return self.email


class Image(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.ImageField(upload_to="images/")
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="images")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    dislikes_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.title


class ImageReaction(models.Model):
    class ReactionType(models.TextChoices):
        LIKE = "like", "Like"
        DISLIKE = "dislike", "Dislike"

    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="image_reactions")
    reaction_type = models.CharField(max_length=7, choices=ReactionType.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["image", "user"], name="unique_image_user_reaction")
        ]

    def __str__(self):
        return f"{self.user.email}: {self.image.title} ({self.reaction_type})"
