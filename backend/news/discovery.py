import re
from urllib.parse import urljoin, urlparse

from .fetching import fetch_html
from .parsing import clean_title, extract_page_title, html_to_text, title_from_text
from .security import ensure_public_web_url
from .summaries import prepare_article_summary



MAX_NEWS_ITEMS = 6

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
