from django.conf import settings
from django.db import models


class NewsSource(models.Model):
    name = models.CharField(max_length=120)
    url = models.URLField(unique=True)
    is_active = models.BooleanField(default=True)
    search_news = models.BooleanField(default=True)
    search_calendars = models.BooleanField(default=False)
    search_tables = models.BooleanField(default=False)
    summary = models.TextField(blank=True)
    last_error = models.TextField(blank=True)
    last_fetched_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="news_sources",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class NewsItem(models.Model):
    source = models.ForeignKey(NewsSource, on_delete=models.CASCADE, related_name="items")
    title = models.CharField(max_length=220)
    url = models.URLField()
    summary = models.TextField()
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["source", "url"], name="unique_news_item_per_source_url"),
        ]

    def __str__(self):
        return self.title


class SourceDiscovery(models.Model):
    class DiscoveryType(models.TextChoices):
        CALENDAR = "calendar", "Kalender"
        TABLE = "table", "Tabelle"

    source = models.ForeignKey(NewsSource, on_delete=models.CASCADE, related_name="discoveries")
    discovery_type = models.CharField(max_length=20, choices=DiscoveryType.choices)
    title = models.CharField(max_length=220)
    url = models.URLField()
    description = models.TextField(blank=True)
    is_imported = models.BooleanField(default=False)
    show_on_main_page = models.BooleanField(default=True)
    import_error = models.TextField(blank=True)
    imported_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["discovery_type", "title"]
        constraints = [
            models.UniqueConstraint(
                fields=["source", "discovery_type", "url"],
                name="unique_source_discovery",
            ),
        ]

    def __str__(self):
        return self.title


class ImportedExternalItem(models.Model):
    class ItemType(models.TextChoices):
        CALENDAR = "calendar", "Kalender"
        TABLE = "table", "Tabelle"

    discovery = models.ForeignKey(SourceDiscovery, on_delete=models.CASCADE, related_name="imported_items")
    item_type = models.CharField(max_length=20, choices=ItemType.choices)
    title = models.CharField(max_length=220)
    starts_at = models.DateTimeField(blank=True, null=True)
    ends_at = models.DateTimeField(blank=True, null=True)
    content = models.TextField(blank=True)
    source_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["item_type", "starts_at", "title"]

    def __str__(self):
        return self.title
