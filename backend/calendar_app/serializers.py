from rest_framework import serializers

from .models import CalendarEvent


class CalendarEventSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = CalendarEvent
        fields = (
            "id",
            "group",
            "title",
            "description",
            "starts_at",
            "ends_at",
            "location",
            "visibility",
            "tags",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_by", "created_at", "updated_at")
