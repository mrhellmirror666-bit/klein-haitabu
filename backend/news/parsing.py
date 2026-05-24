import csv
import io
import re
from datetime import datetime, timezone as datetime_timezone
from html import unescape

from common.dates import parse_german_date_from_text



MAX_IMPORTED_ITEMS = 12

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



def parse_ics_events(text):
    from .summaries import format_calendar_summary

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
    sample = "\n".join(line for line in text.splitlines() if line.strip())[:2048]

    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,")
        reader = csv.reader(io.StringIO(text), dialect)
    except csv.Error:
        reader = csv.reader(io.StringIO(text), delimiter=";", skipinitialspace=True)

    for row in reader:
        columns = [column.strip() for column in row if column.strip()]
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
        if len(rows) >= MAX_IMPORTED_ITEMS:
            break

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
    from .summaries import format_calendar_summary

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

def html_to_text(html):
    html = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\1>", " ", html)
    html = re.sub(r'(?is)<a\b[^>]*href=["\'][^"\']+["\'][^>]*>(.*?)</a>', r"\1", html)
    html = re.sub(r"(?is)<br\s*/?>", "\n", html)
    html = re.sub(r"(?is)</p>", "\n", html)
    html = re.sub(r"(?is)<.*?>", " ", html)
    html = unescape(html)
    html = re.sub(r"\s+", " ", html)
    return html.strip()

def strip_urls(text):
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"www\.\S+", " ", text)
    text = re.sub(r"\b\S+\.(de|com|org|net|eu|info|io)\S*", " ", text)
    return re.sub(r"\s+", " ", text).strip()
