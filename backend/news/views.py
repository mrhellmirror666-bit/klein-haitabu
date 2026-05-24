from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from common.models import Group

from .forms import NewsSourceForm
from .models import ImportedExternalItem, NewsItem, NewsSource, SourceDiscovery
from .services import discover_news_items, discover_source_links, import_discovery_items


class AdminOnlyMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_platform_admin


class NewsSourceListView(AdminOnlyMixin, ListView):
    model = NewsSource
    template_name = "news/source_list.html"
    context_object_name = "sources"

    def get_queryset(self):
        return NewsSource.objects.select_related("target_group").prefetch_related("items", "discoveries__target_group").order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["target_group_choices"] = [("", "Alle Gruppen"), *Group.objects.filter(is_active=True).values_list("pk", "name")]
        return context


class NewsSourceCreateView(AdminOnlyMixin, CreateView):
    model = NewsSource
    form_class = NewsSourceForm
    template_name = "news/source_form.html"
    success_url = reverse_lazy("news:source-list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Nachrichtenquelle wurde angelegt.")
        return super().form_valid(form)


class NewsSourceUpdateView(AdminOnlyMixin, UpdateView):
    model = NewsSource
    form_class = NewsSourceForm
    template_name = "news/source_form.html"
    success_url = reverse_lazy("news:source-list")

    def form_valid(self, form):
        messages.success(self.request, "Nachrichtenquelle wurde aktualisiert.")
        return super().form_valid(form)


class NewsSourceDeleteView(AdminOnlyMixin, DeleteView):
    model = NewsSource
    template_name = "news/source_confirm_delete.html"
    success_url = reverse_lazy("news:source-list")


class NewsSourceSummarizeView(AdminOnlyMixin, View):
    def post(self, request, pk):
        source = NewsSource.objects.get(pk=pk)

        try:
            created_or_updated, found_links = refresh_source(source)
            messages.success(
                request,
                f"{source.name}: {created_or_updated} Nachrichten und {found_links} Hinweise wurden aktualisiert.",
            )
        except Exception as exc:
            source.last_error = str(exc)
            source.save(update_fields=["last_error", "updated_at"])
            messages.error(request, f"{source.name} konnte nicht durchsucht werden: {exc}")

        return redirect("news:source-list")


def refresh_source(source):
    discovered_items = discover_news_items(source.url) if source.search_news else []
    discovered_links = discover_source_links(
        source.url,
        search_calendars=source.search_calendars,
        search_tables=source.search_tables,
    )
    created_or_updated = 0
    found_links = 0

    for item in discovered_items:
        NewsItem.objects.update_or_create(
            source=source,
            url=item["url"],
            defaults={
                "title": item["title"],
                "summary": item["summary"],
            },
        )
        created_or_updated += 1

    for link in discovered_links:
        SourceDiscovery.objects.update_or_create(
            source=source,
            discovery_type=link["type"],
            url=link["url"],
            defaults={
                "target_group": source.target_group,
                "title": link["title"],
                "description": link["description"],
            },
        )
        found_links += 1

    source.summary = f"{created_or_updated} Nachrichten und {found_links} Kalender-/Tabellenhinweise wurden gefunden."
    source.last_error = ""
    source.last_fetched_at = timezone.now()
    source.save(update_fields=["summary", "last_error", "last_fetched_at", "updated_at"])
    return created_or_updated, found_links


class NewsSourceBulkApplyView(AdminOnlyMixin, View):
    def post(self, request):
        updated_sources = 0
        refreshed_sources = 0

        source_ids = request.POST.getlist("source_ids")
        discovery_ids = request.POST.getlist("discovery_ids")

        for source in NewsSource.objects.filter(pk__in=source_ids):
            source.is_active = request.POST.get(f"source_{source.pk}_is_active") == "on"
            source.target_group_id = request.POST.get(f"source_{source.pk}_target_group") or None
            source.search_news = request.POST.get(f"source_{source.pk}_search_news") == "on"
            source.search_calendars = request.POST.get(f"source_{source.pk}_search_calendars") == "on"
            source.search_tables = request.POST.get(f"source_{source.pk}_search_tables") == "on"
            source.save(
                update_fields=[
                    "is_active",
                    "target_group",
                    "search_news",
                    "search_calendars",
                    "search_tables",
                    "updated_at",
                ]
            )
            updated_sources += 1

            try:
                refresh_source(source)
                refreshed_sources += 1
            except Exception as exc:
                source.last_error = str(exc)
                source.save(update_fields=["last_error", "updated_at"])

        for discovery in SourceDiscovery.objects.filter(pk__in=discovery_ids):
            discovery.show_on_main_page = request.POST.get(f"discovery_{discovery.pk}_show_on_main_page") == "on"
            discovery.target_group_id = request.POST.get(f"discovery_{discovery.pk}_target_group") or None
            discovery.save(update_fields=["show_on_main_page", "target_group", "updated_at"])

        messages.success(
            request,
            f"Aenderungen wurden gespeichert. {refreshed_sources} von {updated_sources} Quellen wurden aktualisiert.",
        )
        return redirect("news:source-list")


class SourceDiscoveryImportView(AdminOnlyMixin, View):
    def post(self, request, pk):
        discovery = SourceDiscovery.objects.select_related("source").get(pk=pk)

        try:
            ImportedExternalItem.objects.filter(discovery=discovery).delete()
            imported_items = import_discovery_items(discovery)

            for item in imported_items:
                ImportedExternalItem.objects.create(
                    discovery=discovery,
                    item_type=item["item_type"],
                    title=item["title"],
                    starts_at=item["starts_at"],
                    ends_at=item["ends_at"],
                    content=item["content"],
                    source_url=discovery.url,
                )

            discovery.is_imported = True
            discovery.import_error = ""
            discovery.imported_at = timezone.now()
            discovery.save(update_fields=["is_imported", "import_error", "imported_at", "updated_at"])
            messages.success(request, f"{discovery.title}: {len(imported_items)} Eintraege wurden importiert.")
        except Exception as exc:
            discovery.import_error = str(exc)
            discovery.save(update_fields=["import_error", "updated_at"])
            messages.error(request, f"{discovery.title} konnte nicht importiert werden: {exc}")

        return redirect("news:source-list")


class SourceDiscoveryDeleteImportView(AdminOnlyMixin, View):
    def post(self, request, pk):
        discovery = SourceDiscovery.objects.get(pk=pk)
        deleted_count, _ = ImportedExternalItem.objects.filter(discovery=discovery).delete()

        discovery.is_imported = False
        discovery.imported_at = None
        discovery.import_error = ""
        discovery.save(update_fields=["is_imported", "imported_at", "import_error", "updated_at"])

        messages.success(request, f"Import fuer {discovery.title} wurde geloescht ({deleted_count} Eintraege).")
        return redirect("news:source-list")


class SourceDiscoveryDisplayUpdateView(AdminOnlyMixin, View):
    def post(self, request, pk):
        discovery = SourceDiscovery.objects.get(pk=pk)
        discovery.show_on_main_page = request.POST.get("show_on_main_page") == "on"
        discovery.save(update_fields=["show_on_main_page", "updated_at"])

        messages.success(request, f"Anzeige fuer {discovery.title} wurde gespeichert.")
        return redirect("news:source-list")
