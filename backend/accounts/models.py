from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        USER = "user", "Nutzer"
        GUEST = "guest", "Gast"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.GUEST)

    @property
    def is_platform_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_read_only_guest(self):
        return self.role == self.Role.GUEST and not self.is_superuser

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.ADMIN
            self.is_staff = True
        elif self.role == self.Role.GUEST:
            self.is_staff = False

        super().save(*args, **kwargs)
