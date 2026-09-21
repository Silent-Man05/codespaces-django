from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('guest', 'Guest'),
    )

    USER_STATUS_CHOICES = (
         ('active', 'Active'), ('blocked', 'Blocked'),
    )

    # Role field
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="guest")
    # User status field 
    user_status = models.CharField(max_length=10, choices=USER_STATUS_CHOICES, default="active")
    # Shared fields
    first_name  = models.CharField(max_length=100)
    last_name  = models.CharField(max_length=100)
    address = models.TextField(blank=True, null=True)

    phone_number = models.CharField(max_length=20, blank=True, null=True)
    image = models.ImageField(upload_to="user_images/", blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Image(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    images = models.ImageField(upload_to="images/")

    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="images")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title




class ImageReaction(models.Model):
    REACTION_CHOICES = [
        ('like', 'Like'),
        ('dislike', 'Dislike'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name="reactions")
    reaction = models.CharField(max_length=10, choices=REACTION_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'image')

    def __str__(self):
        return f"{self.user.username} {self.reaction} {self.image.title}"



