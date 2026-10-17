from django.urls import path

from apps.core.api import health

urlpatterns = [
    path("api/v1/health", health, name="health"),
]
