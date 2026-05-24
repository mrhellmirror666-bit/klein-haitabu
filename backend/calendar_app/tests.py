from datetime import datetime

from django.test import TestCase
from django.utils import timezone

from calendar_app.forms import CalendarEventForm
from calendar_app.views import default_event_start_from_text, default_location_from_text
from accounts.models import User
from calendar_app.forms import CalendarEventForm
from calendar_app.models import CalendarEvent


class CalendarEventModelTests(TestCase):
    def test_event_string_is_title(self):
        user = User.objects.create_user(username="user", password="testpass123")
        event = CalendarEvent.objects.create(
            title="Mitgliederversammlung",
            starts_at=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.get_current_timezone()),
            ends_at=datetime(2026, 6, 1, 11, 0, tzinfo=timezone.get_current_timezone()),
            created_by=user,
        )

        self.assertEqual(str(event), "Mitgliederversammlung")


class CalendarEventFormTests(TestCase):
    def test_end_must_be_after_start(self):
        form = CalendarEventForm(
            data={
                "title": "Fehlerhafter Termin",
                "starts_at": "2026-06-01T11:00",
                "ends_at": "2026-06-01T10:00",
                "description": "",
                "location": "",
            }
        )

        self.assertFalse(form.is_valid())


class EventInitialDateTests(TestCase):
    def test_numeric_german_date_is_used_for_initial_start(self):
        starts_at = default_event_start_from_text("Wann: 24.05.2026, 18:30 Uhr")

        self.assertEqual(starts_at.day, 24)
        self.assertEqual(starts_at.month, 5)
        self.assertEqual(starts_at.year, 2026)
        self.assertEqual(starts_at.hour, 18)
        self.assertEqual(starts_at.minute, 30)

    def test_written_german_month_is_used_for_initial_start(self):
        starts_at = default_event_start_from_text("Termin am 24. Mai 2026")

        self.assertEqual(starts_at.day, 24)
        self.assertEqual(starts_at.month, 5)
        self.assertEqual(starts_at.year, 2026)

    def test_location_is_read_from_where_line(self):
        location = default_location_from_text("Wann: 20.03.2026\nWo: Baden-Wuerttemberg, 72351 Geislingen")

        self.assertEqual(location, "Baden-Wuerttemberg, 72351 Geislingen")

    def test_datetime_local_initial_value_is_rendered_for_browser(self):
        starts_at = default_event_start_from_text("Wann: 20.03.2026")
        form = CalendarEventForm(initial={"starts_at": starts_at, "ends_at": starts_at})

        self.assertIn('value="2026-03-20T09:00"', str(form["starts_at"]))
