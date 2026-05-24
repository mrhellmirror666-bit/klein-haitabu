from django import forms

from common.models import Group

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["target_group"].queryset = Group.objects.filter(is_active=True)
        self.fields["target_group"].empty_label = "Alle Gruppen"
