from django.urls import path

from apps.accounts.views import login, logout, me, permissions
from apps.core.api import health

urlpatterns = [
    path("api/v1/health", health, name="health"),
    path("api/v1/auth/login", login, name="auth-login"),
    path("api/v1/auth/logout", logout, name="auth-logout"),
    path("api/v1/auth/me", me, name="auth-me"),
    path("api/v1/auth/permissions", permissions, name="auth-permissions"),
]
