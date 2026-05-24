from django.contrib import admin

from .models import ImportedExternalItem, NewsItem, NewsSource, SourceDiscovery


@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "url", "is_active", "target_group", "search_news", "search_calendars", "search_tables", "last_fetched_at")
    list_filter = ("is_active", "target_group", "search_news", "search_calendars", "search_tables")
    search_fields = ("name", "url", "summary")


@admin.register(NewsItem)
class NewsItemAdmin(admin.ModelAdmin):
    list_display = ("title", "source", "published_at", "created_at")
    list_filter = ("source",)
    search_fields = ("title", "summary", "url")


@admin.register(SourceDiscovery)
class SourceDiscoveryAdmin(admin.ModelAdmin):
    list_display = ("title", "source", "discovery_type", "target_group", "is_imported", "show_on_main_page", "updated_at")
    list_filter = ("discovery_type", "target_group", "is_imported", "show_on_main_page", "source")
    search_fields = ("title", "description", "url")


@admin.register(ImportedExternalItem)
class ImportedExternalItemAdmin(admin.ModelAdmin):
    list_display = ("title", "item_type", "starts_at", "discovery")
    list_filter = ("item_type", "discovery__source")
    search_fields = ("title", "content", "source_url")
