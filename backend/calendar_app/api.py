from rest_framework import permissions, viewsets

from accounts.permissions import can_create_event, can_edit_event

from .models import CalendarEvent
from .serializers import CalendarEventSerializer


class CalendarEventPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return can_create_event(request.user)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return can_edit_event(request.user, obj)


class CalendarEventViewSet(viewsets.ModelViewSet):
    queryset = CalendarEvent.objects.select_related("created_by")
    serializer_class = CalendarEventSerializer
    permission_classes = [CalendarEventPermission]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
