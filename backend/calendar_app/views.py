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
from news.models import ImportedExternalItem, NewsItem

from .forms import CalendarEventForm, NewsToCalendarEventForm
from .models import CalendarEvent


def default_event_start_from_text(text):
    parsed_date = parse_german_date(text)
    if parsed_date:
        hour, minute = parse_time(text)
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


def parse_german_date(text):
    numeric_match = re.search(r"\b(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{2,4})\b", text)
    if numeric_match:
        day, month, year = numeric_match.groups()
        if len(year) == 2:
            year = f"20{year}"
        return date(int(year), int(month), int(day))

    word_match = re.search(
        r"\b(\d{1,2})\.\s*(Januar|Februar|Maerz|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+(\d{4})\b",
        text,
        flags=re.IGNORECASE,
    )
    if word_match:
        day, month_name, year = word_match.groups()
        return date(int(year), german_month_number(month_name), int(day))

    return None


def parse_time(text):
    match = re.search(r"\b(\d{1,2}):(\d{2})\b", text)
    if match:
        return int(match.group(1)), int(match.group(2))

    match = re.search(r"\b(\d{1,2})\.(\d{2})\s*Uhr\b", text, flags=re.IGNORECASE)
    if match:
        return int(match.group(1)), int(match.group(2))

    return 9, 0


def german_month_number(month_name):
    normalized = month_name.lower().replace("ä", "ae")
    months = {
        "januar": 1,
        "februar": 2,
        "maerz": 3,
        "märz": 3,
        "april": 4,
        "mai": 5,
        "juni": 6,
        "juli": 7,
        "august": 8,
        "september": 9,
        "oktober": 10,
        "november": 11,
        "dezember": 12,
    }
    return months[normalized]


class EventListView(LoginRequiredMixin, ListView):
    model = CalendarEvent
    template_name = "calendar_app/event_list.html"
    context_object_name = "events"
    group_code = CalendarEvent.Group.KLEIN_HAITABU
    group_name = "Klein Haitabu"
    list_url_name = "calendar:list"
    create_url_name = "calendar:create"

    def get_queryset(self):
        return CalendarEvent.objects.filter(group=self.group_code).select_related("created_by")

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

        context.update(
            {
                "calendar_weeks": weeks,
                "month_date": month_date,
                "previous_month": previous_month,
                "next_month": next_month,
                "weekday_labels": ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
                "group_code": self.group_code,
                "group_name": self.group_name,
                "create_url_name": self.create_url_name,
                "news_items": NewsItem.objects.filter(source__is_active=True)
                .select_related("source")
                .order_by("-updated_at")[:6],
                "imported_items": ImportedExternalItem.objects.filter(
                    discovery__is_imported=True,
                    discovery__show_on_main_page=True,
                )
                .filter(visible_imports)
                .select_related("discovery", "discovery__source")
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
    group_code = CalendarEvent.Group.KLEIN_HAITABU
    success_url_name = "calendar:list"

    def dispatch(self, request, *args, **kwargs):
        if not can_create_event(request.user):
            raise PermissionDenied("Du darfst keine Termine erstellen.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.group = self.group_code
        messages.success(self.request, "Termin wurde erstellt.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(self.success_url_name)


class NewsToCalendarEventCreateView(LoginRequiredMixin, CreateView):
    model = CalendarEvent
    form_class = NewsToCalendarEventForm
    template_name = "calendar_app/news_event_form.html"
    group_code = CalendarEvent.Group.KLEIN_HAITABU
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
        form.instance.group = self.group_code
        messages.success(self.request, "Kurznachricht wurde als Kalendereintrag gespeichert.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(self.success_url_name)


class ImportToCalendarEventCreateView(LoginRequiredMixin, CreateView):
    model = CalendarEvent
    form_class = NewsToCalendarEventForm
    template_name = "calendar_app/news_event_form.html"
    group_code = CalendarEvent.Group.KLEIN_HAITABU
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
        form.instance.group = self.group_code
        messages.success(self.request, "Import wurde als Kalendereintrag gespeichert.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(self.success_url_name)


class EventUpdateView(LoginRequiredMixin, UpdateView):
    model = CalendarEvent
    form_class = CalendarEventForm
    template_name = "calendar_app/event_form.html"
    def get_success_url(self):
        if self.object.group == CalendarEvent.Group.DSF:
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
        if self.object.group == CalendarEvent.Group.DSF:
            return reverse_lazy("calendar:dsf-list")
        return reverse_lazy("calendar:list")

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not can_edit_event(request.user, self.object):
            raise PermissionDenied("Du darfst diesen Termin nicht loeschen.")
        return super().dispatch(request, *args, **kwargs)


class DSFEventListView(EventListView):
    group_code = CalendarEvent.Group.DSF
    group_name = "DSF"
    list_url_name = "calendar:dsf-list"
    create_url_name = "calendar:dsf-create"


class DSFEventCreateView(EventCreateView):
    group_code = CalendarEvent.Group.DSF
    success_url_name = "calendar:dsf-list"


class DSFNewsToCalendarEventCreateView(NewsToCalendarEventCreateView):
    group_code = CalendarEvent.Group.DSF
    success_url_name = "calendar:dsf-list"


class DSFImportToCalendarEventCreateView(ImportToCalendarEventCreateView):
    group_code = CalendarEvent.Group.DSF
    success_url_name = "calendar:dsf-list"
