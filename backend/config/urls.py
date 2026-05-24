from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView


urlpatterns = [
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("admin/", admin.site.urls),
    path("konto/", include("accounts.urls")),
    path("kalender/", include("calendar_app.urls")),
    path("nachrichten/", include("news.urls")),
    path("api/", include("calendar_app.api_urls")),
]
