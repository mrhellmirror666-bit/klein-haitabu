from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView


urlpatterns = [
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("gruppen/dsf/", TemplateView.as_view(template_name="groups/dsf.html"), name="group-dsf"),
    path(
        "gruppen/hyperraum-hopfen/",
        TemplateView.as_view(template_name="groups/hyperraum_hopfen.html"),
        name="group-hyperraum-hopfen",
    ),
    path("admin/", admin.site.urls),
    path("konto/", include("accounts.urls")),
    path("kalender/", include("calendar_app.urls")),
    path("nachrichten/", include("news.urls")),
    path("api/", include("calendar_app.api_urls")),
]
