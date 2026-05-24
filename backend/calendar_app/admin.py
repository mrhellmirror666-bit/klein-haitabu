from django.contrib import admin

from .models import CalendarEvent


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ("title", "group", "starts_at", "ends_at", "visibility", "created_by")
    list_filter = ("group", "starts_at", "visibility", "created_by")
    search_fields = ("title", "description", "location", "tags")
