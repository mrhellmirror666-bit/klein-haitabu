# Backup- und Update-Plan

Dieser Plan sichert das Projekt regelmaessig und holt Updates aus GitHub erst
nach einem frischen Backup.

## Was gesichert wird

Das Backup-Skript `scripts/backup-project.ps1` erstellt ein ZIP-Archiv mit:

- Projektdateien
- lokaler SQLite-Datenbank `backend/db.sqlite3`
- lokaler Konfiguration `.env`
- Dokumentation und Docker-Dateien

Ausgeschlossen werden erzeugte oder sehr grosse Ordner wie `.git`, `.venv`,
`__pycache__` und `staticfiles`.

Wichtig: Das Backup kann Zugangsdaten aus `.env` enthalten. Deshalb gehoert der
Backup-Ordner nicht in einen oeffentlichen Cloud-Ordner ohne Schutz.

## Manuelles Backup

```powershell
.\scripts\backup-project.ps1
```

Standardziel:

```text
C:\Users\Helmi\Documents\Klein Haitabu Backups
```

Alte Backups werden standardmaessig nach 30 Tagen entfernt.

## Manuelles Update aus GitHub

```powershell
.\scripts\update-from-github.ps1
```

Ablauf:

1. Backup erstellen.
2. Pruefen, ob lokale Aenderungen vorhanden sind.
3. Neue Version von `origin/main` holen.
4. Nur dann aktualisieren, wenn Git ohne Zusammenfuehrung aktualisieren kann.

Wenn lokale Aenderungen vorhanden sind, stoppt das Update. Das verhindert, dass
eigene Arbeit versehentlich ueberschrieben wird.

## Automatische Windows-Aufgaben einrichten

PowerShell als normaler Benutzer im Projektordner starten:

```powershell
.\scripts\install-windows-tasks.ps1
```

Falls Windows dabei "Zugriff verweigert" meldet, PowerShell ausserhalb dieser
App oder als Administrator oeffnen und den Befehl erneut ausfuehren.

Danach laufen zwei Aufgaben:

- taegliches Backup um 03:00 Uhr
- woechentliches GitHub-Update sonntags um 03:30 Uhr

Andere Zeiten sind moeglich:

```powershell
.\scripts\install-windows-tasks.ps1 -BackupTime "02:00" -UpdateTime "02:30"
```

## Quellen automatisch aktualisieren

Nachrichtenquellen koennen ausserhalb des Browser-Requests aktualisiert werden:

```powershell
cd backend
python manage.py refresh_sources
```

Eine einzelne Quelle kann per ID aktualisiert werden:

```powershell
python manage.py refresh_sources --pk 3
```

Fehler einer Quelle werden in der Quelle gespeichert und brechen die
Aktualisierung der anderen Quellen nicht ab. Der Befehl eignet sich fuer eine
geplante Aufgabe, zum Beispiel im Windows Task Scheduler.

## Voraussetzungen

- Git for Windows muss installiert sein.
- Das Repository nutzt aktuell:

```text
https://github.com/mrhellmirror666-bit/klein-haitabu.git
```

Wenn `git` nicht gefunden wird, Git for Windows installieren und danach ein
neues PowerShell-Fenster oeffnen.

## Wiederherstellung

1. Gewuenschtes ZIP aus dem Backup-Ordner entpacken.
2. Projektdateien zurueckkopieren.
3. Bei Bedarf `.env` und `backend/db.sqlite3` aus dem Backup uebernehmen.
4. Anwendung neu starten.

Vor jeder Wiederherstellung empfiehlt sich ein zusaetzliches Backup des
aktuellen Stands.
