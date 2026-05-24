import calendar
from datetime import date, timedelta
import re

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from accounts.permissions import can_create_event, can_edit_event
from common.dates import parse_german_date_from_text, parse_time_from_text
from common.models import Group
from news.models import ImportedExternalItem, NewsItem, NewsSource

from .forms import CalendarEventForm, NewsToCalendarEventForm
from .models import CalendarEvent

GROUP_KLEIN_HAITABU = "klein_haitabu"
GROUP_DSF = "dsf"


def default_event_start_from_text(text):
    parsed_date = parse_german_date_from_text(text)
    if parsed_date:
        hour, minute = parse_time_from_text(text)
        has_time = re.search(r"\b\d{1,2}:\d{2}\b|\b\d{1,2}\.\d{2}\s*Uhr\b", text, flags=re.IGNORECASE)
        if (hour, minute) == (0, 0) and not has_time:
            hour, minute = 9, 0
        return timezone.make_aware(
            timezone.datetime(parsed_date.year, parsed_date.month, parsed_date.day, hour, minute),
            timezone.get_current_timezone(),
        )

    return timezone.localtime(timezone.now()).replace(second=0, microsecond=0) + timedelta(days=1)


def default_location_from_text(text):
    match = re.search(r"^Wo:\s*(.+)$", text, flags=re.MULTILINE)
    if match:
        return match.group(1).strip()
    return ""


class EventListView(LoginRequiredMixin, ListView):
    model = CalendarEvent
    template_name = "calendar_app/event_list.html"
    context_object_name = "events"
    group_slug = GROUP_KLEIN_HAITABU
    group_name = "Klein Haitabu"
    list_url_name = "calendar:list"
    create_url_name = "calendar:create"

    def get_queryset(self):
        return CalendarEvent.objects.filter(group__slug=self.group_slug).select_related("created_by", "group")

    def get_month_date(self):
        today = timezone.localdate()
        year = self.request.GET.get("jahr", today.year)
        month = self.request.GET.get("monat", today.month)

        try:
            return date(int(year), int(month), 1)
        except ValueError:
            return today.replace(day=1)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        month_date = self.get_month_date()
        calendar.setfirstweekday(calendar.MONDAY)

        first_weekday, days_in_month = calendar.monthrange(month_date.year, month_date.month)
        start_day = month_date.toordinal() - first_weekday
        weeks = []
        events_by_day = {}

        for event in context["events"]:
            local_day = timezone.localtime(event.starts_at).date()
            events_by_day.setdefault(local_day, []).append(event)

        for week_index in range(6):
            week = []
            for day_index in range(7):
                current_day = date.fromordinal(start_day + week_index * 7 + day_index)
                week.append(
                    {
                        "date": current_day,
                        "day": current_day.day,
                        "is_current_month": current_day.month == month_date.month,
                        "is_today": current_day == timezone.localdate(),
                        "events": events_by_day.get(current_day, []),
                    }
                )
            weeks.append(week)

        previous_month = self.shift_month(month_date, -1)
        next_month = self.shift_month(month_date, 1)

        now = timezone.now()
        visible_imports = (
            Q(item_type=ImportedExternalItem.ItemType.TABLE)
            | Q(item_type=ImportedExternalItem.ItemType.CALENDAR, ends_at__gte=now)
            | Q(item_type=ImportedExternalItem.ItemType.CALENDAR, ends_at__isnull=True, starts_at__gte=now)
        )
        visible_for_group = Q(target_group__isnull=True) | Q(target_group__slug=self.group_slug)

        context.update(
            {
                "calendar_weeks": weeks,
                "month_date": month_date,
                "previous_month": previous_month,
                "next_month": next_month,
                "weekday_labels": ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
                "group_code": self.group_slug,
                "group_name": self.group_name,
                "create_url_name": self.create_url_name,
                "news_items": NewsItem.objects.filter(
                    source__is_active=True,
                )
                .filter(
                    Q(source__target_group__isnull=True) | Q(source__target_group__slug=self.group_slug),
                )
                .select_related("source", "source__target_group")
                .order_by("-updated_at")[:6],
                "imported_items": ImportedExternalItem.objects.filter(
                    discovery__is_imported=True,
                    discovery__show_on_main_page=True,
                )
                .filter(Q(discovery__target_group__isnull=True) | Q(discovery__target_group__slug=self.group_slug))
                .filter(visible_imports)
                .select_related("discovery", "discovery__target_group", "discovery__source")
                .order_by("-created_at")[:8],
            }
        )
        return context

    @staticmethod
    def shift_month(month_date, offset):
        month = month_date.month + offset
        year = month_date.year

        if month < 1:
            return date(year - 1, 12, 1)
        if month > 12:
            return date(year + 1, 1, 1)
        return date(year, month, 1)


class EventCreateView(LoginRequiredMixin, CreateView):
    model = CalendarEvent
    form_class = CalendarEventForm
    template_name = "calendar_app/event_form.html"
    group_slug = GROUP_KLEIN_HAITABU
    success_url_name = "calendar:list"

    def dispatch(self, request, *args, **kwargs):
        if not can_create_event(request.user):
            raise PermissionDenied("Du darfst keine Termine erstellen.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.group = Group.objects.get(slug=self.group_slug)
        messages.success(self.request, "Termin wurde erstellt.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(self.success_url_name)


class NewsToCalendarEventCreateView(LoginRequiredMixin, CreateView):
    model = CalendarEvent
    form_class = NewsToCalendarEventForm
    template_name = "calendar_app/news_event_form.html"
    group_slug = GROUP_KLEIN_HAITABU
    success_url_name = "calendar:list"

    def dispatch(self, request, *args, **kwargs):
        if not can_create_event(request.user):
            raise PermissionDenied("Du darfst keine Termine erstellen.")
        self.news_item = NewsItem.objects.select_related("source").get(pk=kwargs["news_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        starts_at = default_event_start_from_text(f"{self.news_item.title} {self.news_item.summary}")
        ends_at = starts_at + timedelta(hours=1)
        return {
            "title": self.news_item.title[:200],
            "description": self.news_item.summary,
            "starts_at": starts_at,
            "ends_at": ends_at,
            "location": default_location_from_text(self.news_item.summary),
            "visibility": CalendarEvent.Visibility.USERS,
            "tags": "Nachricht, Import",
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["source_title"] = self.news_item.title
        context["source_text"] = self.news_item.summary
        context["source_label"] = "Kurznachricht"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.group = Group.objects.get(slug=self.group_slug)
        messages.success(self.request, "Kurznachricht wurde als Kalendereintrag gespeichert.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(self.success_url_name)


class ImportToCalendarEventCreateView(LoginRequiredMixin, CreateView):
    model = CalendarEvent
    form_class = NewsToCalendarEventForm
    template_name = "calendar_app/news_event_form.html"
    group_slug = GROUP_KLEIN_HAITABU
    success_url_name = "calendar:list"

    def dispatch(self, request, *args, **kwargs):
        if not can_create_event(request.user):
            raise PermissionDenied("Du darfst keine Termine erstellen.")
        self.imported_item = ImportedExternalItem.objects.select_related("discovery", "discovery__source").get(
            pk=kwargs["import_pk"]
        )
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        starts_at = self.imported_item.starts_at or default_event_start_from_text(
            f"{self.imported_item.title} {self.imported_item.content}"
        )
        ends_at = self.imported_item.ends_at or starts_at + timedelta(hours=1)
        return {
            "title": self.imported_item.title[:200],
            "description": self.imported_item.content,
            "starts_at": starts_at,
            "ends_at": ends_at,
            "location": default_location_from_text(self.imported_item.content),
            "visibility": CalendarEvent.Visibility.USERS,
            "tags": f"{self.imported_item.get_item_type_display()}, Import",
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["source_title"] = self.imported_item.title
        context["source_text"] = self.imported_item.content
        context["source_label"] = "Import"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.group = Group.objects.get(slug=self.group_slug)
        messages.success(self.request, "Import wurde als Kalendereintrag gespeichert.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(self.success_url_name)


class EventUpdateView(LoginRequiredMixin, UpdateView):
    model = CalendarEvent
    form_class = CalendarEventForm
    template_name = "calendar_app/event_form.html"
    def get_success_url(self):
        if self.object.group.slug == GROUP_DSF:
            return reverse_lazy("calendar:dsf-list")
        return reverse_lazy("calendar:list")

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not can_edit_event(request.user, self.object):
            raise PermissionDenied("Du darfst diesen Termin nicht bearbeiten.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Termin wurde aktualisiert.")
        return super().form_valid(form)


class EventDeleteView(LoginRequiredMixin, DeleteView):
    model = CalendarEvent
    template_name = "calendar_app/event_confirm_delete.html"

    def get_success_url(self):
        if self.object.group.slug == GROUP_DSF:
            return reverse_lazy("calendar:dsf-list")
        return reverse_lazy("calendar:list")

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not can_edit_event(request.user, self.object):
            raise PermissionDenied("Du darfst diesen Termin nicht loeschen.")
        return super().dispatch(request, *args, **kwargs)


class DSFEventListView(EventListView):
    group_slug = GROUP_DSF
    group_name = "DSF"
    list_url_name = "calendar:dsf-list"
    create_url_name = "calendar:dsf-create"


class DSFEventCreateView(EventCreateView):
    group_slug = GROUP_DSF
    success_url_name = "calendar:dsf-list"


class DSFNewsToCalendarEventCreateView(NewsToCalendarEventCreateView):
    group_slug = GROUP_DSF
    success_url_name = "calendar:dsf-list"


class DSFImportToCalendarEventCreateView(ImportToCalendarEventCreateView):
    group_slug = GROUP_DSF
    success_url_name = "calendar:dsf-list"
