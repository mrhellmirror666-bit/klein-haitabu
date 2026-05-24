# Erste Schritte

## Aktueller Stand

Die erste Umsetzung ist bereits vorbereitet. Du musst das Django-Projekt nicht
mehr selbst mit `django-admin startproject` erstellen.

Vorhanden sind:

- Projektkonfiguration
- Benutzer-App mit Rollenfeld
- Kalender-App mit Terminmodell
- Login, Logout und Registrierung
- einfache Terminseiten
- erste REST-API
- Docker-Grundstruktur

## Lokale Startbefehle

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd backend
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Danach ist die lokale Testseite normalerweise unter dieser Adresse erreichbar:

```text
http://127.0.0.1:8000/
```

## Empfohlene Umsetzungsreihenfolge

1. Python auf dem Rechner lauffaehig machen.
2. Abhaengigkeiten installieren.
3. Migrationen ausfuehren.
4. Admin-Benutzer anlegen.
5. Erste Testnutzer anlegen.
6. Rollen im Admin-Bereich setzen.
7. Termine erstellen und Rechte testen.
8. Kalenderansicht mit FullCalendar verbessern.
9. News-Widget ergaenzen.
10. VPS-Deployment vorbereiten.

## Erstes Ziel

Das erste kleine Erfolgserlebnis sollte sein:

> Ein Benutzer kann sich anmelden und einen Termin im Kalender sehen.

Danach wird Schritt fuer Schritt erweitert.
