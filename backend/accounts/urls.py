from django.contrib.auth import views as auth_views
from django.urls import path

from .views import PermissionManagementView, RegisterView


urlpatterns = [
    path("registrieren/", RegisterView.as_view(), name="register"),
    path("rechte/", PermissionManagementView.as_view(), name="permission-management"),
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
