from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class User(AbstractUser):
    ROLE_USER = "user"
    ROLE_OPERATOR = "operator"
    ROLE_ADMIN = "admin"
    ROLE_CHOICES = [
        (ROLE_USER, "普通用户"),
        (ROLE_OPERATOR, "运营"),
        (ROLE_ADMIN, "超级管理员"),
    ]
    STATUS_ACTIVE = "active"
    STATUS_DISABLED = "disabled"
    STATUS_CHOICES = [(STATUS_ACTIVE, "启用"), (STATUS_DISABLED, "停用")]

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_USER)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def save(self, *args, **kwargs):
        self.is_active = self.status == self.STATUS_ACTIVE
        super().save(*args, **kwargs)
