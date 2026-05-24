# Klein Haitabu Vereinsplattform

Projektvorlage fuer eine moderne, sichere und wartbare Vereinsplattform.

## Ziel

Diese Webanwendung soll einem Verein eine gemeinsame Plattform bieten:

- gemeinsamer Kalender
- Benutzerregistrierung und Login
- Rollenmodell mit Admin, Nutzer und Gast
- responsives Design fuer Desktop und Mobilgeraete
- spaetere Schnittstellen fuer Outlook, Excel, Google Kalender und REST-API

## Empfohlener Tech-Stack

| Bereich | Empfehlung |
| --- | --- |
| Backend | Django |
| Frontend | Django Templates, HTMX, Tailwind CSS |
| Kalender-Oberflaeche | FullCalendar |
| API | Django REST Framework |
| Datenbank | PostgreSQL |
| Deployment | Docker Compose auf Linux-VPS |
| Reverse Proxy / HTTPS | Caddy |

## Warum diese Auswahl?

Django bringt viele wichtige Funktionen schon mit: Benutzerverwaltung, Login,
Passwortsicherheit, Admin-Bereich, Datenbankzugriff und Schutzmechanismen gegen
haeufige Angriffe. Dadurch muss weniger sicherheitskritischer Code selbst
geschrieben werden.

HTMX und klassische Django Templates halten die erste Version einfach. Eine
spaetere Erweiterung mit React oder Next.js bleibt moeglich, ist fuer den Start
aber nicht noetig.

## Geplante Ordnerstruktur

```text
vereinsplattform/
  backend/
    config/
    accounts/
    calendar_app/
    common/
    templates/
    static/
  docker/
    caddy/
  docs/
  docker-compose.yml
  .env.example
  .gitignore
  README.md
```

## Dokumentation

- [Architektur](docs/ARCHITEKTUR.md)
- [Backup- und Update-Plan](docs/BACKUP_UND_UPDATES.md)
- [Datenbankmodell](docs/DATENBANKMODELL.md)
- [Rollenmodell](docs/ROLLENMODELL.md)
- [Sicherheitskonzept](docs/SICHERHEIT.md)
- [Schnittstellenkonzept](docs/SCHNITTSTELLEN.md)
- [VPS-Deployment](docs/VPS_DEPLOYMENT.md)
- [Erste Schritte](docs/ERSTE_SCHRITTE.md)

## Aktueller Stand

Die erste Django-Struktur ist bereits angelegt:

- eigenes Benutzer-Modell mit Rollenfeld
- Registrierung, Login und Logout
- Terminmodell fuer den Kalender
- Terminliste, Terminformular, Bearbeiten und Loeschen
- einfache Rechtepruefung fuer Admin, Nutzer und Gast
- erste REST-API fuer Termine
- Docker-Grundgeruest mit PostgreSQL und Caddy

## Lokal starten

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd backend
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Danach ist die Anwendung unter `http://127.0.0.1:8000/` erreichbar.

Hinweis: Auf diesem Rechner war Python beim Erstellen der Vorlage noch nicht
ueber die Befehle `python` oder `py` verfuegbar. Falls der Start nicht klappt,
muss zuerst Python installiert oder die Windows-Store-Verknuepfung korrigiert
werden.

## Mit Docker starten

```powershell
docker compose up --build
```

Danach laeuft die Anwendung ueber Caddy. Fuer den echten VPS muessen in `.env`
starke Passwoerter, ein neuer `DJANGO_SECRET_KEY` und die echte Domain gesetzt
werden.
"# klein-haitabu" 
