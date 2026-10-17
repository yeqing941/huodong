from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.accounts.views import token_for


class UserAndAuditApiTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email="admin@example.com", username="admin", password="secret", role="admin")
        self.operator = User.objects.create_user(email="operator@example.com", username="operator", password="secret", role="operator")
        self.user = User.objects.create_user(email="user@example.com", username="user", password="secret", role="user")

    def auth(self, user):
        return {"HTTP_AUTHORIZATION": f"Bearer {token_for(user)}"}

    def test_admin_can_change_role_and_disable_without_delete(self):
        response = self.client.patch(reverse("user-detail", args=[self.user.pk]), {"role": "operator"}, content_type="application/json", **self.auth(self.admin))
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, "operator")
        response = self.client.post(reverse("user-disable", args=[self.user.pk]), **self.auth(self.admin))
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.status, "disabled")
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_operator_and_user_cannot_manage_users_or_audit(self):
        for actor in (self.operator, self.user):
            self.assertEqual(self.client.get(reverse("users"), **self.auth(actor)).status_code, 403)
            self.assertEqual(self.client.get(reverse("audit-logs"), **self.auth(actor)).status_code, 403)

    def test_audit_log_query_filters(self):
        AuditLog.objects.create(actor=self.admin, action="role_update", object_type="user", object_id=str(self.user.pk), success=True, before_data={"role": "user"}, after_data={"role": "operator"})
        AuditLog.objects.create(actor=self.admin, action="login_failure", object_type="auth", object_id="", success=False)
        response = self.client.get(reverse("audit-logs") + "?action=role_update&object_type=user", **self.auth(self.admin))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["total"], 1)
        self.assertEqual(response.json()["data"]["items"][0]["action"], "role_update")

    def test_user_change_writes_audit_log(self):
        self.client.patch(reverse("user-detail", args=[self.user.pk]), {"role": "operator"}, content_type="application/json", **self.auth(self.admin))
        log = AuditLog.objects.get(action="role_update")
        self.assertEqual(log.actor_id, self.admin.pk)
        self.assertEqual(log.object_type, "user")
        self.assertEqual(log.before_data["role"], "user")
        self.assertEqual(log.after_data["role"], "operator")
