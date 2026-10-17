from django.urls import path

from apps.accounts.views import login, logout, me, permissions
from apps.activities.views import activity_detail, activities, favorite, favorites, game_types, tags
from apps.activities.views_write import archive_activity, restore_activity
from apps.core.api import health

urlpatterns = [
    path("api/v1/health", health, name="health"),
    path("api/v1/auth/login", login, name="auth-login"),
    path("api/v1/auth/logout", logout, name="auth-logout"),
    path("api/v1/auth/me", me, name="auth-me"),
    path("api/v1/auth/permissions", permissions, name="auth-permissions"),
    path("api/v1/activities", activities, name="activities"),
    path("api/v1/activities/<int:activity_id>", activity_detail, name="activity-detail"),
    path("api/v1/activities/<int:activity_id>/favorite", favorite, name="activity-favorite"),
    path("api/v1/favorites", favorites, name="favorites"),
    path("api/v1/tags", tags, name="tags"),
    path("api/v1/game-types", game_types, name="game-types"),
    path(
        "api/v1/activities/<int:activity_id>/archive",
        archive_activity,
        name="activity-archive",
    ),
    path(
        "api/v1/activities/<int:activity_id>/restore",
        restore_activity,
        name="activity-restore",
    ),
]
