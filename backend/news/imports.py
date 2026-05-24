from datetime import datetime, timezone as datetime_timezone
from urllib.parse import urlparse

from .fetching import fetch_text, normalize_webcal_url
from .parsing import MAX_IMPORTED_ITEMS, parse_csv_rows, parse_html_calendar_items, parse_html_table_rows, parse_ics_events
from .security import ensure_public_web_url



def import_discovery_items(discovery):
    if discovery.discovery_type == "calendar":
        return import_calendar_items(discovery.url)
    if discovery.discovery_type == "table":
        return import_table_items(discovery.url)
    return []

def import_calendar_items(url):
    ensure_public_web_url(normalize_webcal_url(url))
    text = fetch_text(normalize_webcal_url(url))
    events = parse_ics_events(text)

    if not events:
        events = parse_html_calendar_items(text)

    if not events:
        raise ValueError(
            "In dieser Kalenderquelle wurden keine Termine gefunden. "
            "Wenn es eine iCal-/ICS-Exportadresse gibt, fuege bitte diese als Quelle hinzu."
        )

    upcoming_events = filter_upcoming_calendar_items(events)
    if not upcoming_events:
        raise ValueError("In dieser Kalenderquelle wurden keine zukuenftigen Termine gefunden.")

    return upcoming_events[:MAX_IMPORTED_ITEMS]

def filter_upcoming_calendar_items(items, now=None):
    now = now or datetime.now(datetime_timezone.utc)
    return [item for item in items if calendar_item_is_upcoming(item, now)]

def calendar_item_is_upcoming(item, now):
    ends_at = item.get("ends_at")
    starts_at = item.get("starts_at")

    if ends_at:
        return ends_at >= now
    if starts_at:
        return starts_at >= now
    return False

def import_table_items(url):
    ensure_public_web_url(url)
    parsed = urlparse(url)

    if parsed.path.lower().endswith((".xlsx", ".xls")):
        raise ValueError("Excel-Import wird als naechster Schritt vorbereitet. CSV- und HTML-Tabellen funktionieren bereits.")

    text = fetch_text(url)
    if parsed.path.lower().endswith(".csv"):
        rows = parse_csv_rows(text)
    else:
        rows = parse_html_table_rows(text)

    if not rows:
        raise ValueError("In dieser Tabellenquelle wurden keine lesbaren Zeilen gefunden.")

    return rows[:MAX_IMPORTED_ITEMS]
