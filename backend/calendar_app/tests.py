from datetime import datetime

from django.test import TestCase
from django.utils import timezone

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
