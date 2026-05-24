# VPS-Deployment

## Zielarchitektur

```text
Internet
  -> Domain
    -> Caddy mit HTTPS
      -> Django-App
        -> PostgreSQL
```

## Schritte auf dem VPS

1. Ubuntu-LTS-Server bereitstellen.
2. Eigenen Benutzer fuer die Verwaltung anlegen.
3. SSH-Zugang per Schluessel einrichten.
4. Passwort-Login per SSH deaktivieren.
5. Firewall aktivieren.
6. Nur SSH, HTTP und HTTPS erlauben.
7. Docker und Docker Compose installieren.
8. Projekt auf den Server kopieren oder per Git klonen.
9. `.env` fuer Produktionswerte anlegen.
10. Container starten.
11. Datenbankmigrationen ausfuehren.
12. Statische Dateien sammeln.
13. Admin-Benutzer anlegen.
14. Backups einrichten.

## Reverse Proxy

Caddy ist fuer den Start angenehm, weil HTTPS-Zertifikate automatisch erstellt
und erneuert werden koennen.

Beispielhafte Caddy-Idee:

```text
vereinsdomain.de {
  reverse_proxy web:8000
}
```

## Wichtige Produktionswerte

In der Produktion gelten:

```text
DEBUG=False
DJANGO_SECRET_KEY=ein-langer-geheimer-wert
DATABASE_URL=postgres://...
ALLOWED_HOSTS=vereinsdomain.de,www.vereinsdomain.de
```

Diese Werte gehoeren in eine `.env`-Datei auf dem Server.

## Statische Dateien

Vor dem Start im Produktionsmodus muessen die statischen Dateien gesammelt
werden:

```bash
python manage.py collectstatic --noinput
```

WhiteNoise liefert diese Dateien anschliessend auch ohne separate Caddy-Regel
aus. Caddy kann weiterhin als Reverse Proxy vor Django laufen.
