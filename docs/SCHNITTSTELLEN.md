# Schnittstellenkonzept

## Ziel

Die Plattform soll spaeter Daten mit externen Programmen austauschen koennen.
Dafuer werden interne Daten sauber modelliert und ueber eine REST-API erreichbar
gemacht.

## REST-API

Geplante erste Endpunkte:

```text
GET    /api/events/
POST   /api/events/
GET    /api/events/{id}/
PATCH  /api/events/{id}/
DELETE /api/events/{id}/
```

Die API muss dieselben Rechte beachten wie die Weboberflaeche. Ein Gast darf
also auch per API keine Termine loeschen.

## Kalenderstandards

| Zweck | Standard |
| --- | --- |
| einfacher Kalenderexport | iCalendar / .ics |
| Kalender-Synchronisierung | CalDAV |
| Google Kalender | Google Calendar API oder CalDAV |
| Microsoft Outlook / Exchange | Microsoft Graph API oder iCalendar |

## Excel

Fuer Excel-Import und -Export sollte `.xlsx` verwendet werden. In Python eignet
sich dafuer spaeter zum Beispiel `openpyxl`.

Moegliche Exporte:

- Terminliste
- Mitgliederliste
- Teilnehmerliste

## OAuth2

OAuth2 wird spaeter wichtig, wenn externe Dienste wie Google oder Microsoft
angebunden werden. Am Anfang muss das noch nicht eingebaut werden. Wichtig ist
aber, die Anwendung so zu strukturieren, dass externe Zugangsdaten niemals im
Code stehen, sondern sicher als Konfiguration gespeichert werden.
