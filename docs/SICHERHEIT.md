# Sicherheitskonzept

## Grundregeln

- Passwoerter niemals selbst speichern oder verschluesseln.
- Django-Authentifizierung und Passwort-Hashing verwenden.
- HTTPS auf dem Server erzwingen.
- Formulare mit CSRF-Schutz absichern.
- Eingaben im Backend pruefen.
- Datenbankzugriff ueber Django ORM statt selbst gebauter SQL-Texte.
- Rechte immer im Backend pruefen, nicht nur in der Oberflaeche.
- Geheimnisse in `.env` speichern und nicht ins Git-Repository aufnehmen.

## Wichtige Django-Einstellungen fuer Produktion

```python
# DEBUG darf auf dem Server niemals True sein.
DEBUG = False

# Hier stehen spaeter deine erlaubten Domains.
ALLOWED_HOSTS = ["example.org", "www.example.org"]

# Cookies werden nur ueber HTTPS gesendet.
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Browser sollen Cookies nicht leicht per JavaScript auslesen koennen.
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Schutz gegen Clickjacking.
X_FRAME_OPTIONS = "DENY"
```

## Admin-Bereich

Empfehlungen:

- starkes Passwort verwenden
- Admin-Zugang nicht mit alltaeglichem Nutzerkonto vermischen
- optional Zwei-Faktor-Login spaeter ergaenzen
- optional Zugriff auf `/admin/` per IP beschraenken

## Backups

Mindestens sichern:

- PostgreSQL-Datenbank
- hochgeladene Dateien
- `.env` getrennt und sicher aufbewahren

Backups sollten regelmaessig getestet werden. Ein Backup ist erst dann wirklich
brauchbar, wenn eine Wiederherstellung einmal ausprobiert wurde.
