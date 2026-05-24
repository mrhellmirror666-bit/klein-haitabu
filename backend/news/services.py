import ipaddress
import re
import socket
from datetime import datetime, timezone as datetime_timezone
from html import unescape
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from common.dates import parse_german_date_from_text


MAX_DOWNLOAD_BYTES = 250_000
REQUEST_TIMEOUT_SECONDS = 8
MAX_NEWS_ITEMS = 6
MAX_IMPORTED_ITEMS = 12

NEWS_HINTS = (
    "news",
    "nachricht",
    "presse",
    "artikel",
    "meldung",
    "aktuelles",
    "blog",
)

CALENDAR_HINTS = (
    "calendar",
    "kalender",
    "ical",
    "ics",
    "caldav",
    "termine",
    "veranstaltungen",
    "events",
)

TABLE_HINTS = (
    "table",
    "tabelle",
    "xlsx",
    "xls",
    "csv",
    "excel",
    "liste",
    "download",
)

GERMAN_STATES = (
    "Baden-Wuerttemberg",
    "Baden-Württemberg",
    "Bayern",
    "Berlin",
    "Brandenburg",
    "Bremen",
    "Hamburg",
    "Hessen",
    "Mecklenburg-Vorpommern",
    "Niedersachsen",
    "Nordrhein-Westfalen",
    "Rheinland-Pfalz",
    "Saarland",
    "Sachsen",
    "Sachsen-Anhalt",
    "Schleswig-Holstein",
    "Thueringen",
    "Thüringen",
)


def summarize_source(url):
    ensure_public_web_url(url)
    html = fetch_html(url)
    title = extract_page_title(html)
    text = html_to_text(html)
    summary = prepare_article_summary(title, text)

    if not summary:
        raise ValueError("Aus dieser Seite konnte kein lesbarer Text erkannt werden.")

    return summary


def discover_news_items(source_url):
    ensure_public_web_url(source_url)
    html = fetch_html(source_url)
    candidates = extract_link_candidates(html, source_url)

    if not candidates:
        text = html_to_text(html)
        return [
            {
                "title": title_from_text(text) or "Nachricht",
                "url": source_url,
                "summary": prepare_article_summary(title_from_text(text), text),
            }
        ]

    items = []
    seen_urls = set()

    for candidate in candidates:
        if candidate["url"] in seen_urls:
            continue

        seen_urls.add(candidate["url"])
        try:
            ensure_public_web_url(candidate["url"])
            article_html = fetch_html(candidate["url"])
            article_title = extract_page_title(article_html) or candidate["title"]
            article_text = html_to_text(article_html)
            summary = prepare_article_summary(article_title, article_text)
        except Exception:
            article_text = candidate["title"]
            summary = prepare_article_summary(candidate["title"], article_text)

        if not summary:
            continue

        items.append(
            {
                "title": candidate["title"][:220],
                "url": candidate["url"],
                "summary": summary,
            }
        )

        if len(items) >= MAX_NEWS_ITEMS:
            break

    return items


def discover_source_links(source_url, search_calendars=False, search_tables=False):
    ensure_public_web_url(source_url)
    html = fetch_html(source_url)
    discoveries = []

    if search_calendars:
        discoveries.extend(extract_discovery_candidates(html, source_url, "calendar", CALENDAR_HINTS))

    if search_tables:
        discoveries.extend(extract_discovery_candidates(html, source_url, "table", TABLE_HINTS))

    return discoveries


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


def normalize_webcal_url(url):
    if url.startswith("webcal://"):
        return "https://" + url.removeprefix("webcal://")
    return url


def fetch_text(url):
    request = Request(
        url,
        headers={
            "User-Agent": "Klein-Haitabu-NewsBot/0.1",
            "Accept": "text/calendar,text/csv,text/html,application/xhtml+xml,text/plain,*/*",
        },
    )

    with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        raw = response.read(MAX_DOWNLOAD_BYTES)

    return raw.decode("utf-8", errors="ignore")


def parse_ics_events(text):
    events = []
    blocks = re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", text, flags=re.DOTALL)

    for block in blocks:
        title = read_ics_value(block, "SUMMARY") or "Kalendertermin"
        description = read_ics_value(block, "DESCRIPTION")
        starts_at = parse_ics_datetime(read_ics_value(block, "DTSTART"))
        ends_at = parse_ics_datetime(read_ics_value(block, "DTEND"))

        events.append(
            {
                "item_type": "calendar",
                "title": clean_title(title),
                "starts_at": starts_at,
                "ends_at": ends_at,
                "content": format_calendar_summary(title, description, starts_at, ends_at),
            }
        )

    return events


def read_ics_value(block, key):
    match = re.search(rf"^{key}(?:;[^:]*)?:(.*)$", block, flags=re.MULTILINE)
    if not match:
        return ""
    return unescape_ics_value(match.group(1).strip())


def unescape_ics_value(value):
    return value.replace("\\n", " ").replace("\\,", ",").replace("\\;", ";").strip()


def parse_ics_datetime(value):
    if not value:
        return None

    value = value.strip()
    if len(value) == 8:
        parsed = datetime.strptime(value, "%Y%m%d")
        return parsed.replace(tzinfo=datetime_timezone.utc)

    if value.endswith("Z"):
        parsed = datetime.strptime(value, "%Y%m%dT%H%M%SZ")
        return parsed.replace(tzinfo=datetime_timezone.utc)

    try:
        parsed = datetime.strptime(value[:15], "%Y%m%dT%H%M%S")
        return parsed.replace(tzinfo=datetime_timezone.utc)
    except ValueError:
        return None


def parse_csv_rows(text):
    rows = []
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line in lines[:MAX_IMPORTED_ITEMS]:
        columns = [column.strip().strip('"') for column in re.split(r";|,", line) if column.strip()]
        if not columns:
            continue
        rows.append(
            {
                "item_type": "table",
                "title": clean_title(columns[0]) or "Tabellenzeile",
                "starts_at": None,
                "ends_at": None,
                "content": " | ".join(columns[:8]),
            }
        )

    return rows


def parse_html_table_rows(html):
    rows = []
    row_matches = re.findall(r"(?is)<tr[^>]*>(.*?)</tr>", html)

    for row in row_matches[:MAX_IMPORTED_ITEMS]:
        cells = re.findall(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>", row)
        values = [html_to_text(cell) for cell in cells if html_to_text(cell)]
        if not values:
            continue
        rows.append(
            {
                "item_type": "table",
                "title": clean_title(values[0]) or "Tabellenzeile",
                "starts_at": None,
                "ends_at": None,
                "content": " | ".join(values[:8]),
            }
        )

    return rows


def parse_html_calendar_items(html):
    text = html_to_text(html)
    snippets = split_text_around_dates(text)
    events = []

    for snippet in snippets:
        starts_at = parse_german_date_from_text(snippet)
        title = title_from_calendar_snippet(snippet)

        if not starts_at or not title:
            continue

        events.append(
            {
                "item_type": "calendar",
                "title": title,
                "starts_at": starts_at,
                "ends_at": None,
                "content": format_calendar_summary(title, snippet, starts_at, None),
            }
        )

    return events


def split_text_around_dates(text):
    date_pattern = (
        r"\b\d{1,2}\.\s*\d{1,2}\.\s*\d{2,4}\b"
        r"|\b\d{1,2}\.\s*(Januar|Februar|Maerz|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+\d{4}\b"
    )
    matches = list(re.finditer(date_pattern, text, flags=re.IGNORECASE))
    snippets = []

    for match in matches:
        start = max(0, match.start() - 120)
        end = min(len(text), match.end() + 260)
        snippets.append(text[start:end].strip())

    return snippets


def title_from_calendar_snippet(snippet):
    clean = strip_urls(snippet)
    clean = re.sub(r"\b\d{1,2}\.\s*\d{1,2}\.\s*\d{2,4}\b", " ", clean)
    clean = re.sub(
        r"\b\d{1,2}\.\s*(Januar|Februar|Maerz|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+\d{4}\b",
        " ",
        clean,
        flags=re.IGNORECASE,
    )
    clean = re.sub(r"\b\d{1,2}[:.]\d{2}\s*(Uhr)?\b", " ", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s+", " ", clean).strip()

    if not clean:
        return "Importierter Termin"

    words = clean.split()
    return clean_title(" ".join(words[:14]))


def format_calendar_summary(title, text, starts_at=None, ends_at=None):
    clean = strip_urls(text)
    parts = [
        f"Wann: {format_when(clean, starts_at, ends_at)}",
        f"Wo: {extract_where(clean)}",
        f"Kurz: {mini_calendar_summary(title, clean)}",
    ]
    return "\n".join(parts)


def format_when(text, starts_at=None, ends_at=None):
    date_text = extract_date_text(text)
    time_text = extract_opening_or_time_text(text)

    if not date_text and starts_at:
        date_text = starts_at.strftime("%d.%m.%Y")

    if not time_text and starts_at and starts_at.hour:
        time_text = starts_at.strftime("%H:%M Uhr")

    if ends_at and starts_at and ends_at != starts_at:
        time_text = f"{starts_at.strftime('%H:%M Uhr')} bis {ends_at.strftime('%H:%M Uhr')}"

    if date_text and time_text:
        return f"{date_text}, {time_text}"
    if date_text:
        return date_text
    if time_text:
        return time_text
    return "nicht erkannt"


def extract_date_text(text):
    match = re.search(r"\b\d{1,2}\.\s*\d{1,2}\.\s*\d{2,4}\b", text)
    if match:
        return re.sub(r"\s+", "", match.group(0))

    match = re.search(
        r"\b\d{1,2}\.\s*(Januar|Februar|Maerz|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+\d{4}\b",
        text,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group(0)

    return ""


def extract_opening_or_time_text(text):
    opening_match = re.search(
        r"((Einlass|Oeffnungszeiten|Öffnungszeiten|Beginn|Start)[^.!?]{0,80})",
        text,
        flags=re.IGNORECASE,
    )
    if opening_match:
        return clean_title(opening_match.group(1))

    range_match = re.search(r"\b\d{1,2}[:.]\d{2}\s*(Uhr)?\s*(-|bis)\s*\d{1,2}[:.]\d{2}\s*(Uhr)?\b", text)
    if range_match:
        return range_match.group(0)

    time_match = re.search(r"\b\d{1,2}[:.]\d{2}\s*Uhr\b", text, flags=re.IGNORECASE)
    if time_match:
        return time_match.group(0)

    return ""


def extract_where(text):
    state = extract_german_state(text)
    place = extract_postcode_place(text)

    if state and place:
        return f"{state}, {place}"
    if place:
        return place
    if state:
        return state
    return "nicht erkannt"


def extract_german_state(text):
    lowered = text.lower()
    for state in GERMAN_STATES:
        if state.lower() in lowered:
            return state
    return ""


def extract_postcode_place(text):
    match = re.search(r"\b(\d{5})\s+([A-ZÄÖÜ][A-Za-zÄÖÜäöüß\-.]+(?:\s+[A-ZÄÖÜ][A-Za-zÄÖÜäöüß\-.]+){0,2})", text)
    if match:
        return f"{match.group(1)} {match.group(2)}"
    return ""


def mini_calendar_summary(title, text):
    clean = strip_calendar_noise(text)
    keywords = extract_event_keywords(clean)

    if keywords:
        return keywords

    fallback = title or clean
    words = fallback.split()
    if not words:
        return "keine kurze Beschreibung erkannt"
    return clean_title(" ".join(words[:24]))


def strip_calendar_noise(text):
    clean = strip_urls(text)
    clean = re.sub(r"\b\d{1,2}\.\s*\d{1,2}\.\s*\d{2,4}\b", " ", clean)
    clean = re.sub(r"\b\d{5}\s+[A-ZÄÖÜ][A-Za-zÄÖÜäöüß\-.]+(?:\s+[A-ZÄÖÜ][A-Za-zÄÖÜäöüß\-.]+){0,2}", " ", clean)
    for state in GERMAN_STATES:
        clean = re.sub(re.escape(state), " ", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\b\d{1,2}[:.]\d{2}\s*(Uhr)?\b", " ", clean, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", clean).strip()


def extract_event_keywords(text):
    lowered = text.lower()
    pieces = []

    event_terms = [
        ("mittelaltermarkt", "ein Mittelaltermarkt"),
        ("weihnachtsmarkt", "ein Weihnachtsmarkt"),
        ("markt", "ein Markt"),
        ("festival", "ein Festival"),
        ("konzert", "ein Konzert"),
        ("lager", "ein Lager"),
        ("turnier", "ein Turnier"),
    ]
    feature_terms = [
        ("einlasskontrolle", "mit Einlasskontrolle"),
        ("livemusik", "mit Livemusik"),
        ("live-musik", "mit Livemusik"),
        ("ritterturnier", "als Highlight gibt es ein Ritterturnier"),
        ("rittertunier", "als Highlight gibt es ein Ritterturnier"),
        ("ritter tunier", "als Highlight gibt es ein Ritterturnier"),
        ("handwerk", "mit Handwerk"),
        ("lagerleben", "mit Lagerleben"),
    ]

    for needle, phrase in event_terms:
        if needle in lowered:
            pieces.append(phrase)
            break

    for needle, phrase in feature_terms:
        if needle in lowered and phrase not in pieces:
            pieces.append(phrase)

    if pieces:
        sentence = ", ".join(pieces)
        return sentence[0].upper() + sentence[1:] + "."

    return ""


def extract_discovery_candidates(html, base_url, discovery_type, hints):
    pattern = re.compile(r'(?is)<a\b[^>]*href=["\'](?P<href>[^"\']+)["\'][^>]*>(?P<label>.*?)</a>')
    candidates = []
    seen_urls = set()

    for match in pattern.finditer(html):
        href = match.group("href").strip()
        label = html_to_text(match.group("label"))
        absolute_url = urljoin(base_url, href)
        parsed = urlparse(absolute_url)

        if parsed.scheme not in {"http", "https", "webcal"}:
            continue

        haystack = f"{parsed.path} {parsed.query} {label}".lower()
        if not any(hint in haystack for hint in hints):
            continue

        if absolute_url in seen_urls:
            continue

        seen_urls.add(absolute_url)
        title = clean_title(label) or fallback_title_for_discovery(discovery_type, absolute_url)
        candidates.append(
            {
                "type": discovery_type,
                "title": title,
                "url": absolute_url,
                "description": describe_discovery(discovery_type, absolute_url),
            }
        )

    return candidates[:12]


def fallback_title_for_discovery(discovery_type, url):
    parsed = urlparse(url)
    filename = parsed.path.rstrip("/").split("/")[-1]
    if filename:
        return clean_title(filename.replace("-", " ").replace("_", " "))
    return "Kalender" if discovery_type == "calendar" else "Tabelle"


def describe_discovery(discovery_type, url):
    parsed = urlparse(url)
    path = parsed.path.lower()

    if discovery_type == "calendar":
        if path.endswith(".ics"):
            return "iCalendar-Datei gefunden. Diese kann spaeter fuer Kalenderimporte genutzt werden."
        return "Moeglicher Kalender- oder Terminbereich gefunden."

    if path.endswith((".xlsx", ".xls")):
        return "Excel-Datei gefunden. Diese kann spaeter fuer Tabellenimporte genutzt werden."
    if path.endswith(".csv"):
        return "CSV-Datei gefunden. Diese kann spaeter fuer Tabellenimporte genutzt werden."
    return "Moeglicher Tabellen- oder Listenbereich gefunden."


def extract_link_candidates(html, base_url):
    pattern = re.compile(r'(?is)<a\b[^>]*href=["\'](?P<href>[^"\']+)["\'][^>]*>(?P<label>.*?)</a>')
    candidates = []

    for match in pattern.finditer(html):
        href = match.group("href").strip()
        label = html_to_text(match.group("label"))
        absolute_url = urljoin(base_url, href)

        if not is_probable_news_link(absolute_url, label):
            continue

        title = clean_title(label)
        if not title:
            continue

        candidates.append({"title": title, "url": absolute_url})

    return candidates[:20]


def is_probable_news_link(url, label):
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False

    haystack = f"{parsed.path} {label}".lower()
    if len(label.strip()) < 18:
        return False

    return any(hint in haystack for hint in NEWS_HINTS)


def clean_title(text):
    text = re.sub(r"\s+", " ", text).strip()
    return text[:220]


def title_from_text(text):
    words = text.split()
    if not words:
        return ""
    return " ".join(words[:12])


def extract_page_title(html):
    title_match = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
    if title_match:
        return clean_title(html_to_text(title_match.group(1)))

    heading_match = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", html)
    if heading_match:
        return clean_title(html_to_text(heading_match.group(1)))

    return ""


def prepare_article_summary(title, text):
    clean_text = strip_urls(text)
    clean_title = strip_urls(title)

    if clean_title:
        clean_text = remove_repeated_title(clean_text, clean_title)

    summary = make_short_summary(clean_text)
    if clean_title and summary:
        return f"{clean_title}: {summary}"
    if clean_title:
        return clean_title
    return summary


def strip_urls(text):
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"www\.\S+", " ", text)
    text = re.sub(r"\b\S+\.(de|com|org|net|eu|info|io)\S*", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def remove_repeated_title(text, title):
    normalized_title = re.escape(title.strip())
    return re.sub(rf"^\s*{normalized_title}\s*", "", text, flags=re.IGNORECASE).strip()


def ensure_public_web_url(url):
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Nur http- und https-Adressen sind erlaubt.")

    if not parsed.hostname:
        raise ValueError("Die Internetadresse ist unvollstaendig.")

    for result in socket.getaddrinfo(parsed.hostname, None):
        ip = ipaddress.ip_address(result[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise ValueError("Interne oder lokale Adressen sind aus Sicherheitsgruenden nicht erlaubt.")


def fetch_html(url):
    request = Request(
        url,
        headers={
            "User-Agent": "Klein-Haitabu-NewsBot/0.1",
            "Accept": "text/html,application/xhtml+xml",
        },
    )

    with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        content_type = response.headers.get("content-type", "")
        if "html" not in content_type:
            raise ValueError("Die Quelle liefert keine HTML-Webseite.")

        raw = response.read(MAX_DOWNLOAD_BYTES)

    return raw.decode("utf-8", errors="ignore")


def html_to_text(html):
    html = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\1>", " ", html)
    html = re.sub(r'(?is)<a\b[^>]*href=["\'][^"\']+["\'][^>]*>(.*?)</a>', r"\1", html)
    html = re.sub(r"(?is)<br\s*/?>", "\n", html)
    html = re.sub(r"(?is)</p>", "\n", html)
    html = re.sub(r"(?is)<.*?>", " ", html)
    html = unescape(html)
    html = re.sub(r"\s+", " ", html)
    return html.strip()


def make_short_summary(text):
    text = strip_urls(text)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    useful_sentences = [sentence.strip() for sentence in sentences if len(sentence.strip()) > 60]
    summary = " ".join(useful_sentences[:2])
    if not summary and len(text) > 60:
        summary = text.strip()
    return summary[:900]
