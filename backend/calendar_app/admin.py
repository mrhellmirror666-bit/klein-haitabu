from django.contrib import admin

from .models import CalendarEvent


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ("title", "starts_at", "ends_at", "created_by")
    list_filter = ("starts_at", "created_by")
    search_fields = ("title", "description", "location")
