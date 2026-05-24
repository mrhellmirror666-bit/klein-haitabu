from django import forms

from .models import CalendarEvent


class CalendarEventForm(forms.ModelForm):
    class Meta:
        model = CalendarEvent
        fields = ("title", "description", "starts_at", "ends_at", "location", "visibility", "tags")
        labels = {
            "title": "Titel",
            "description": "Text",
            "starts_at": "Start",
            "ends_at": "Ende",
            "location": "Ort",
            "visibility": "Sichtbar fuer",
            "tags": "Tags",
        }
        help_texts = {
            "visibility": "Nutzer: nur angemeldete normale Nutzer und Admins. Gaeste: auch Gastkonten. Oeffentlich: spaeter ohne Account sichtbar.",
            "tags": "Mehrere Tags mit Komma trennen, zum Beispiel: Markt, Mittelalter, Musik.",
        }
        widgets = {
            "starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["starts_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["ends_at"].input_formats = ["%Y-%m-%dT%H:%M"]

    def clean(self):
        cleaned_data = super().clean()
        starts_at = cleaned_data.get("starts_at")
        ends_at = cleaned_data.get("ends_at")

        if starts_at and ends_at and ends_at <= starts_at:
            raise forms.ValidationError("Das Ende muss nach dem Start liegen.")

        return cleaned_data


class NewsToCalendarEventForm(CalendarEventForm):
    pass
