# Architektur

## Grundidee

Die erste Version wird als klassische Django-Webanwendung gebaut. Das bedeutet:

- Django liefert HTML-Seiten aus.
- HTMX macht einzelne Bereiche der Seite interaktiv, ohne ein grosses
  JavaScript-Frontend zu benoetigen.
- PostgreSQL speichert Benutzer, Rollen und Termine.
- Django REST Framework stellt spaeter eine saubere API bereit.

## Systemuebersicht

```text
Browser / Mobilgeraet
  -> HTTPS
    -> Caddy Reverse Proxy
      -> Django Anwendung
        -> PostgreSQL Datenbank
```

## Apps im Django-Projekt

### accounts

Zustaendig fuer:

- Benutzer
- Registrierung
- Login und Logout
- Rollen
- Rechtepruefungen

### calendar_app

Zustaendig fuer:

- Kalendertermine
- Terminansicht
- Terminbearbeitung
- API-Endpunkte fuer Termine
- spaeter Import und Export

### common

Zustaendig fuer gemeinsam genutzte Logik:

- Basismodelle
- Hilfsfunktionen
- allgemeine Rechtepruefungen

## Warum kein separates React-Frontend am Anfang?

Ein getrenntes Frontend und Backend erzeugt mehr bewegliche Teile:

- zwei Projekte
- zwei Build-Prozesse
- komplexere Authentifizierung
- mehr Deployment-Aufwand

Fuer eine Einzelperson ist Django mit Templates einfacher zu verstehen, zu
warten und sicher zu betreiben. Eine REST-API wird trotzdem von Anfang an
vorgesehen, damit externe Programme spaeter angebunden werden koennen.
