# Datenbankmodell

## Tabellen fuer die erste Version

### users

Speichert Benutzerkonten.

| Feld | Bedeutung |
| --- | --- |
| id | eindeutige interne ID |
| username | Benutzername |
| email | E-Mail-Adresse |
| password_hash | sicher gespeichertes Passwort |
| role | Rolle: admin, user oder guest |
| is_active | Konto aktiv oder gesperrt |
| date_joined | Registrierungsdatum |

### calendar_events

Speichert Termine.

| Feld | Bedeutung |
| --- | --- |
| id | eindeutige interne ID |
| title | Titel des Termins |
| description | optionale Beschreibung |
| starts_at | Startzeitpunkt |
| ends_at | Endzeitpunkt |
| location | optionaler Ort |
| created_by | Benutzer, der den Termin erstellt hat |
| created_at | Erstellungszeitpunkt |
| updated_at | letzter Aenderungszeitpunkt |

### event_participants

Optional fuer spaetere Teilnehmerlisten.

| Feld | Bedeutung |
| --- | --- |
| id | eindeutige interne ID |
| event_id | zugehoeriger Termin |
| user_id | zugehoeriger Benutzer |
| status | zum Beispiel zugesagt, abgesagt, offen |

## Beispiel: Benutzer-Modell

```python
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # TextChoices begrenzt die erlaubten Rollen auf feste Werte.
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        USER = "user", "Nutzer"
        GUEST = "guest", "Gast"

    # Neue Benutzer starten als Gast.
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.GUEST,
    )
```

## Beispiel: Termin-Modell

```python
from django.conf import settings
from django.db import models


class CalendarEvent(models.Model):
    # Kurzer Name des Termins.
    title = models.CharField(max_length=200)

    # Beschreibung darf leer bleiben.
    description = models.TextField(blank=True)

    # Zeitpunkte sollten immer mit Zeitzone gespeichert werden.
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()

    # Ort ist optional.
    location = models.CharField(max_length=255, blank=True)

    # PROTECT verhindert, dass Termine versehentlich verschwinden,
    # wenn ein Benutzer geloescht werden soll.
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_events",
    )

    # Automatische Zeitstempel.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```
