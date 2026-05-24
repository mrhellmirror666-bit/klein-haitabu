from django.urls import path

from .views import EventCreateView, EventDeleteView, EventListView, EventUpdateView


app_name = "calendar"

urlpatterns = [
    path("", EventListView.as_view(), name="list"),
    path("neu/", EventCreateView.as_view(), name="create"),
    path("<int:pk>/bearbeiten/", EventUpdateView.as_view(), name="update"),
    path("<int:pk>/loeschen/", EventDeleteView.as_view(), name="delete"),
]
