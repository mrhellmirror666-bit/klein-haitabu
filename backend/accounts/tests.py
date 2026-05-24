from datetime import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.forms import RegistrationForm
from accounts.models import User
from accounts.permissions import can_create_event, can_edit_event, can_view_event
from calendar_app.models import CalendarEvent


class RolePermissionTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin", password="testpass123", role=User.Role.ADMIN)
        self.user = User.objects.create_user(username="user", password="testpass123", role=User.Role.USER)
        self.other_user = User.objects.create_user(username="other", password="testpass123", role=User.Role.USER)
        self.guest = User.objects.create_user(username="guest", password="testpass123", role=User.Role.GUEST)
        self.event = CalendarEvent.objects.create(
            title="Probe",
            starts_at=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.get_current_timezone()),
            ends_at=datetime(2026, 6, 1, 11, 0, tzinfo=timezone.get_current_timezone()),
            created_by=self.user,
        )

    def test_admin_and_user_can_create_events(self):
        self.assertTrue(can_create_event(self.admin))
        self.assertTrue(can_create_event(self.user))

    def test_guest_cannot_create_events(self):
        self.assertFalse(can_create_event(self.guest))

    def test_guest_can_view_events(self):
        self.assertTrue(can_view_event(self.guest, self.event))

    def test_admin_can_edit_all_events(self):
        self.assertTrue(can_edit_event(self.admin, self.event))

    def test_user_can_only_edit_own_events(self):
        self.assertTrue(can_edit_event(self.user, self.event))
        self.assertFalse(can_edit_event(self.other_user, self.event))

    def test_guest_cannot_edit_events(self):
        self.assertFalse(can_edit_event(self.guest, self.event))

    def test_superuser_is_treated_as_admin(self):
        superuser = User.objects.create_superuser(username="super", password="testpass123")

        self.assertEqual(superuser.role, User.Role.ADMIN)
        self.assertTrue(can_create_event(superuser))

    def test_guest_cannot_open_event_create_view(self):
        self.client.force_login(self.guest)

        response = self.client.get(reverse("calendar:create"))

        self.assertEqual(response.status_code, 403)

    def test_user_can_open_own_event_edit_view_but_not_foreign_event(self):
        foreign_event = CalendarEvent.objects.create(
            title="Fremder Termin",
            starts_at=datetime(2026, 6, 2, 10, 0, tzinfo=timezone.get_current_timezone()),
            ends_at=datetime(2026, 6, 2, 11, 0, tzinfo=timezone.get_current_timezone()),
            created_by=self.other_user,
        )
        self.client.force_login(self.user)

        own_response = self.client.get(reverse("calendar:update", args=[self.event.pk]))
        foreign_response = self.client.get(reverse("calendar:update", args=[foreign_event.pk]))

        self.assertEqual(own_response.status_code, 200)
        self.assertEqual(foreign_response.status_code, 403)

    def test_admin_can_open_foreign_event_edit_view(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("calendar:update", args=[self.event.pk]))

        self.assertEqual(response.status_code, 200)


class RegistrationFormTests(TestCase):
    def test_registered_users_are_normal_users_by_default(self):
        form = RegistrationForm(
            data={
                "username": "neu",
                "email": "neu@example.org",
                "password1": "EineGuteTestPassphrase123",
                "password2": "EineGuteTestPassphrase123",
            }
        )

        self.assertTrue(form.is_valid())
        user = form.save()

        self.assertEqual(user.role, User.Role.USER)
