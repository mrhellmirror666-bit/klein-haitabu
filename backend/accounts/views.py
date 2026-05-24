from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from .forms import RegistrationForm
from .models import User


class RegisterView(CreateView):
    form_class = RegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("calendar:list")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


class PermissionManagementView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = "accounts/permission_management.html"
    context_object_name = "users"

    def test_func(self):
        return self.request.user.is_platform_admin

    def get_queryset(self):
        return User.objects.order_by("username")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["role_rules"] = [
            {
                "role": "Admin",
                "can_read": "Ja",
                "can_create": "Ja",
                "can_edit": "Ja",
                "can_delete": "Ja",
                "note": "Vollzugriff auf Kalender und Verwaltung.",
            },
            {
                "role": "Nutzer",
                "can_read": "Ja",
                "can_create": "Ja",
                "can_edit": "Eigene",
                "can_delete": "Eigene",
                "note": "Darf eigene Termine verwalten.",
            },
            {
                "role": "Gast",
                "can_read": "Ja",
                "can_create": "Nein",
                "can_edit": "Nein",
                "can_delete": "Nein",
                "note": "Nur lesen. Keine Schreibrechte.",
            },
        ]
        return context
