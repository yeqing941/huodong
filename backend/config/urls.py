from django.urls import path

from apps.accounts.views import login, logout, me, permissions
from apps.accounts.user_views import user_detail, user_state, users
from apps.audit.views import audit_logs
from apps.activities.views import activity_detail, activities, favorite, favorites, game_types, tags
from apps.activities.upload import activity_screenshots
from apps.activities.views_write import archive_activity, activity_import, activity_import_detail, restore_activity
from apps.core.api import health
from apps.taxonomy.views import game_type_detail, game_type_disable, game_types as taxonomy_game_types, tag_detail, tag_disable, tag_merge, tag_migrate, tags as taxonomy_tags
from apps.crawlers.views import configs, config_state, failures, tasks
from apps.reviews.views import admin_review, ai_tag, operator_review, reviews

urlpatterns = [
    path("api/v1/health", health, name="health"),
    path("api/v1/auth/login", login, name="auth-login"),
    path("api/v1/auth/logout", logout, name="auth-logout"),
    path("api/v1/auth/me", me, name="auth-me"),
    path("api/v1/auth/permissions", permissions, name="auth-permissions"),
    path("api/v1/users", users, name="users"),
    path("api/v1/users/<int:user_id>", user_detail, name="user-detail"),
    path("api/v1/users/<int:user_id>/disable", lambda request, user_id: user_state(request, user_id, False), name="user-disable"),
    path("api/v1/users/<int:user_id>/enable", lambda request, user_id: user_state(request, user_id, True), name="user-enable"),
    path("api/v1/audit-logs", audit_logs, name="audit-logs"),
    path("api/v1/activities", activities, name="activities"),
    path("api/v1/activities/<int:activity_id>", activity_detail, name="activity-detail"),
    path("api/v1/activities/<int:activity_id>/favorite", favorite, name="activity-favorite"),
    path("api/v1/activities/<int:activity_id>/screenshots", activity_screenshots, name="activity-screenshots"),
    path("api/v1/activities/import", activity_import, name="activity-import"),
    path("api/v1/activities/import/<int:import_id>", activity_import_detail, name="activity-import-detail"),
    path("api/v1/favorites", favorites, name="favorites"),
    path("api/v1/tags", tags, name="tags"),
    path("api/v1/game-types", game_types, name="game-types"),
    path("api/v1/taxonomy/tags", taxonomy_tags, name="taxonomy-tags"),
    path("api/v1/taxonomy/tags/<int:tag_id>", tag_detail, name="taxonomy-tag-detail"),
    path("api/v1/taxonomy/tags/<int:tag_id>/disable", tag_disable, name="taxonomy-tag-disable"),
    path("api/v1/taxonomy/tags/<int:tag_id>/migrate", tag_migrate, name="taxonomy-tag-migrate"),
    path("api/v1/taxonomy/tags/<int:tag_id>/merge", tag_merge, name="taxonomy-tag-merge"),
    path("api/v1/taxonomy/game-types", taxonomy_game_types, name="taxonomy-game-types"),
    path("api/v1/taxonomy/game-types/<int:game_type_id>", game_type_detail, name="taxonomy-game-type-detail"),
    path("api/v1/taxonomy/game-types/<int:game_type_id>/disable", game_type_disable, name="taxonomy-game-type-disable"),
    path("api/v1/reviews", reviews, name="reviews"),
    path("api/v1/reviews/<int:review_id>", reviews, name="review-detail"),
    path("api/v1/reviews/<int:review_id>/ai-tag", ai_tag, name="review-ai-tag"),
    path("api/v1/reviews/<int:review_id>/operator", operator_review, name="review-operator"),
    path("api/v1/reviews/<int:review_id>/admin", admin_review, name="review-admin"),
    path("api/v1/crawler/configs", configs, name="crawler-configs"),
    path("api/v1/crawler/configs/<int:config_id>", configs, name="crawler-config-detail"),
    path("api/v1/crawler/configs/<int:config_id>/enable", lambda request, config_id: config_state(request, config_id, True), name="crawler-config-enable"),
    path("api/v1/crawler/configs/<int:config_id>/disable", lambda request, config_id: config_state(request, config_id, False), name="crawler-config-disable"),
    path("api/v1/crawler/tasks", tasks, name="crawler-tasks"),
    path("api/v1/crawler/tasks/<int:task_id>", tasks, name="crawler-task-detail"),
    path("api/v1/crawler/tasks/<int:task_id>/retry", lambda request, task_id: tasks(request, task_id, True), name="crawler-task-retry"),
    path("api/v1/crawler/tasks/<int:task_id>/failures", failures, name="crawler-failures"),
    path("api/v1/crawler/tasks/<int:task_id>/failures/<int:failure_id>/retry", failures, name="crawler-failure-retry"),
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
