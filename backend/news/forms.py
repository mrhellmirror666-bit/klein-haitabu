from django import forms

from .models import NewsSource


class NewsSourceForm(forms.ModelForm):
    class Meta:
        model = NewsSource
        fields = ("name", "url", "is_active", "target_group", "search_news", "search_calendars", "search_tables")
        labels = {
            "name": "Name",
            "url": "Internetadresse",
            "is_active": "Im Nachrichtenfenster anzeigen",
            "target_group": "Anzeigen fuer",
            "search_news": "Nachrichten suchen",
            "search_calendars": "Kalender suchen",
            "search_tables": "Tabellen suchen",
        }
