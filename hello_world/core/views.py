from django.shortcuts import render

from .api_views import (
    ImageDetailView,
    ImageListCreateView,
    ImageReactionView,
    LoginView,
    RoleManagementView,
    SignupView,
    VerifyEmailView,
)

def index(request):
    context = {
        "title": "Django example",
    }
    return render(request, "index.html", context)
