from django.conf import settings
from django.db import models


class CalendarEvent(models.Model):
    class Visibility(models.TextChoices):
        USERS = "users", "Nutzer"
        GUESTS = "guests", "Gaeste"
        PUBLIC = "public", "Oeffentlich"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True)
    visibility = models.CharField(max_length=20, choices=Visibility.choices, default=Visibility.USERS)
    tags = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["starts_at"]

    def __str__(self):
        return self.title
