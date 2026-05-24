from django.urls import path

from .views import (
    DSFEventCreateView,
    DSFEventListView,
    DSFImportToCalendarEventCreateView,
    DSFNewsToCalendarEventCreateView,
    EventCreateView,
    EventDeleteView,
    EventListView,
    EventUpdateView,
    ImportToCalendarEventCreateView,
    NewsToCalendarEventCreateView,
)


app_name = "calendar"

urlpatterns = [
    path("", EventListView.as_view(), name="list"),
    path("neu/", EventCreateView.as_view(), name="create"),
    path("neu/aus-nachricht/<int:news_pk>/", NewsToCalendarEventCreateView.as_view(), name="create-from-news"),
    path("neu/aus-import/<int:import_pk>/", ImportToCalendarEventCreateView.as_view(), name="create-from-import"),
    path("dsf/", DSFEventListView.as_view(), name="dsf-list"),
    path("dsf/neu/", DSFEventCreateView.as_view(), name="dsf-create"),
    path("dsf/neu/aus-nachricht/<int:news_pk>/", DSFNewsToCalendarEventCreateView.as_view(), name="dsf-create-from-news"),
    path("dsf/neu/aus-import/<int:import_pk>/", DSFImportToCalendarEventCreateView.as_view(), name="dsf-create-from-import"),
    path("<int:pk>/bearbeiten/", EventUpdateView.as_view(), name="update"),
    path("<int:pk>/loeschen/", EventDeleteView.as_view(), name="delete"),
]
