import calendar
from datetime import date

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from accounts.permissions import can_create_event, can_edit_event

from .forms import CalendarEventForm
from .models import CalendarEvent


class EventListView(LoginRequiredMixin, ListView):
    model = CalendarEvent
    template_name = "calendar_app/event_list.html"
    context_object_name = "events"

    def get_queryset(self):
        return CalendarEvent.objects.select_related("created_by")

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

        context.update(
            {
                "calendar_weeks": weeks,
                "month_date": month_date,
                "previous_month": previous_month,
                "next_month": next_month,
                "weekday_labels": ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
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
    success_url = reverse_lazy("calendar:list")

    def dispatch(self, request, *args, **kwargs):
        if not can_create_event(request.user):
            raise PermissionDenied("Du darfst keine Termine erstellen.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Termin wurde erstellt.")
        return super().form_valid(form)


class EventUpdateView(LoginRequiredMixin, UpdateView):
    model = CalendarEvent
    form_class = CalendarEventForm
    template_name = "calendar_app/event_form.html"
    success_url = reverse_lazy("calendar:list")

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
    success_url = reverse_lazy("calendar:list")

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not can_edit_event(request.user, self.object):
            raise PermissionDenied("Du darfst diesen Termin nicht loeschen.")
        return super().dispatch(request, *args, **kwargs)
