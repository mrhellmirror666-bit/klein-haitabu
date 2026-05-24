from django.urls import path

from .views import (
    NewsSourceCreateView,
    NewsSourceBulkApplyView,
    NewsSourceDeleteView,
    NewsSourceListView,
    NewsSourceSummarizeView,
    NewsSourceUpdateView,
    SourceDiscoveryDeleteImportView,
    SourceDiscoveryDisplayUpdateView,
    SourceDiscoveryImportView,
)


app_name = "news"

urlpatterns = [
    path("", NewsSourceListView.as_view(), name="source-list"),
    path("aenderungen-uebernehmen/", NewsSourceBulkApplyView.as_view(), name="source-bulk-apply"),
    path("neu/", NewsSourceCreateView.as_view(), name="source-create"),
    path("<int:pk>/bearbeiten/", NewsSourceUpdateView.as_view(), name="source-update"),
    path("<int:pk>/loeschen/", NewsSourceDeleteView.as_view(), name="source-delete"),
    path("<int:pk>/zusammenfassen/", NewsSourceSummarizeView.as_view(), name="source-summarize"),
    path("fund/<int:pk>/importieren/", SourceDiscoveryImportView.as_view(), name="discovery-import"),
    path("fund/<int:pk>/import-loeschen/", SourceDiscoveryDeleteImportView.as_view(), name="discovery-delete-import"),
    path("fund/<int:pk>/anzeige-speichern/", SourceDiscoveryDisplayUpdateView.as_view(), name="discovery-display-update"),
]
