from datetime import datetime, timezone

from django.test import TestCase

from news.services import (
    MAX_IMPORTED_ITEMS,
    ensure_public_web_url,
    extract_discovery_candidates,
    filter_upcoming_calendar_items,
    extract_link_candidates,
    extract_page_title,
    html_to_text,
    make_short_summary,
    normalize_webcal_url,
    parse_csv_rows,
    parse_html_calendar_items,
    parse_html_table_rows,
    parse_ics_events,
    prepare_article_summary,
    format_calendar_summary,
)


class NewsServiceTests(TestCase):
    def test_local_addresses_are_blocked(self):
        with self.assertRaises(ValueError):
            ensure_public_web_url("http://127.0.0.1:8000")

    def test_localhost_is_blocked(self):
        with self.assertRaises(ValueError):
            ensure_public_web_url("http://localhost/evil")

    def test_private_network_addresses_are_blocked(self):
        with self.assertRaises(ValueError):
            ensure_public_web_url("http://192.168.1.1/")

    def test_unsupported_url_schemes_are_blocked(self):
        with self.assertRaises(ValueError):
            ensure_public_web_url("ftp://example.com")

    def test_webcal_urls_are_normalized_to_https(self):
        url = normalize_webcal_url("webcal://example.com/cal.ics")

        self.assertEqual(url, "https://example.com/cal.ics")

    def test_html_is_converted_to_text(self):
        text = html_to_text(
            '<html><body><h1>Titel</h1><p>Ein lesbarer Absatz.</p><a href="https://example.org">Linktext</a></body></html>'
        )

        self.assertIn("Titel", text)
        self.assertIn("Ein lesbarer Absatz.", text)
        self.assertIn("Linktext", text)
        self.assertNotIn("https://example.org", text)

    def test_short_summary_uses_readable_sentences(self):
        text = (
            "Das ist ein langer Beispielsatz, der genug Inhalt fuer eine Zusammenfassung liefert. "
            "Ein zweiter langer Satz beschreibt weitere wichtige Informationen fuer die Anzeige."
        )

        summary = make_short_summary(text)

        self.assertIn("Beispielsatz", summary)

    def test_article_summary_uses_title_and_removes_urls(self):
        summary = prepare_article_summary(
            "Vereinsheim wird renoviert",
            "Vereinsheim wird renoviert. Weitere Informationen stehen unter https://example.org/artikel. "
            "Die Arbeiten beginnen im Sommer und betreffen mehrere Raeume des Vereinsheims.",
        )

        self.assertIn("Vereinsheim wird renoviert", summary)
        self.assertNotIn("https://example.org", summary)

    def test_page_title_is_extracted(self):
        title = extract_page_title("<html><head><title>Artikel Titel</title></head><body></body></html>")

        self.assertEqual(title, "Artikel Titel")

    def test_calendar_links_are_discovered(self):
        html = '<a href="/termine/verein.ics">Vereinskalender herunterladen</a>'

        candidates = extract_discovery_candidates(
            html,
            "https://example.org",
            "calendar",
            ("kalender", "termine", "ics"),
        )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["type"], "calendar")

    def test_table_links_are_discovered(self):
        html = '<a href="/downloads/mitglieder.xlsx">Excel Tabelle Mitgliederliste</a>'

        candidates = extract_discovery_candidates(
            html,
            "https://example.org",
            "table",
            ("excel", "tabelle", "xlsx"),
        )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["type"], "table")

    def test_ics_events_are_parsed(self):
        text = """
BEGIN:VCALENDAR
BEGIN:VEVENT
SUMMARY:Vereinstreffen
DTSTART:20260601T180000Z
DTEND:20260601T200000Z
DESCRIPTION:Monatliches Treffen
END:VEVENT
END:VCALENDAR
"""

        events = parse_ics_events(text)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["title"], "Vereinstreffen")
        self.assertEqual(events[0]["item_type"], "calendar")
        self.assertEqual(events[0]["starts_at"], datetime(2026, 6, 1, 18, 0, tzinfo=timezone.utc))
        self.assertEqual(events[0]["ends_at"], datetime(2026, 6, 1, 20, 0, tzinfo=timezone.utc))

    def test_ics_events_with_timezone_parameter_do_not_crash(self):
        text = """
BEGIN:VCALENDAR
BEGIN:VEVENT
SUMMARY:Abendtermin
DTSTART;TZID=Europe/Berlin:20250315T190000
END:VEVENT
END:VCALENDAR
"""

        events = parse_ics_events(text)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["title"], "Abendtermin")

    def test_empty_ics_text_returns_empty_list(self):
        events = parse_ics_events("")

        self.assertEqual(events, [])

    def test_past_calendar_events_are_filtered_from_import(self):
        now = datetime(2026, 5, 24, 12, 0, tzinfo=timezone.utc)
        items = [
            {
                "item_type": "calendar",
                "title": "Alter Termin",
                "starts_at": datetime(2026, 5, 1, 10, 0, tzinfo=timezone.utc),
                "ends_at": datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc),
                "content": "",
            },
            {
                "item_type": "calendar",
                "title": "Laufender Termin",
                "starts_at": datetime(2026, 5, 24, 10, 0, tzinfo=timezone.utc),
                "ends_at": datetime(2026, 5, 24, 13, 0, tzinfo=timezone.utc),
                "content": "",
            },
            {
                "item_type": "calendar",
                "title": "Zukuenftiger Termin",
                "starts_at": datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
                "ends_at": None,
                "content": "",
            },
        ]

        titles = [item["title"] for item in filter_upcoming_calendar_items(items, now=now)]

        self.assertEqual(titles, ["Laufender Termin", "Zukuenftiger Termin"])

    def test_csv_rows_are_parsed(self):
        rows = parse_csv_rows("Name;Rolle\nAnna;Admin")

        self.assertEqual(rows[0]["title"], "Name")
        self.assertIn("Rolle", rows[0]["content"])

    def test_comma_separated_csv_rows_are_parsed(self):
        rows = parse_csv_rows("Name,Rolle\nAnna,Admin")

        self.assertEqual(rows[0]["title"], "Name")
        self.assertEqual(rows[0]["content"], "Name | Rolle")
        self.assertEqual(rows[1]["content"], "Anna | Admin")

    def test_quoted_semicolon_csv_rows_are_parsed(self):
        rows = parse_csv_rows('"Mustermann, Max";"Veranstaltung"')

        self.assertEqual(rows[0]["title"], "Mustermann, Max")
        self.assertEqual(rows[0]["content"], "Mustermann, Max | Veranstaltung")

    def test_empty_csv_rows_are_skipped(self):
        rows = parse_csv_rows("\n\nName;Rolle\n\nAnna;Admin\n")

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["title"], "Name")

    def test_csv_rows_do_not_exceed_import_limit(self):
        text = "\n".join(f"Name {index};Rolle" for index in range(MAX_IMPORTED_ITEMS + 3))

        rows = parse_csv_rows(text)

        self.assertEqual(len(rows), MAX_IMPORTED_ITEMS)

    def test_html_table_rows_are_parsed(self):
        rows = parse_html_table_rows("<table><tr><th>Name</th><th>Rolle</th></tr><tr><td>Anna</td><td>Admin</td></tr></table>")

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]["title"], "Anna")

    def test_html_calendar_dates_are_parsed(self):
        events = parse_html_calendar_items(
            "<html><body><p>Sommerfest am 24.05.2026 um 18:30 Uhr im Vereinsheim.</p></body></html>"
        )

        self.assertEqual(len(events), 1)
        self.assertIn("Sommerfest", events[0]["title"])
        self.assertEqual(events[0]["starts_at"].day, 24)

    def test_calendar_summary_is_limited_to_when_where_and_short_summary(self):
        summary = format_calendar_summary(
            "Mittelaltermarkt",
            "Mittelaltermarkt am 24.05.2026. Oeffnungszeiten 11:00 bis 20:00 Uhr. "
            "Nordrhein-Westfalen 32423 Minden. Ein Mittelaltermarkt mit Einlasskontrolle "
            "und Livemusik. Als Highlight gibt es ein Rittertunier.",
        )

        self.assertIn("Wann:", summary)
        self.assertIn("24.05.2026", summary)
        self.assertIn("Wo:", summary)
        self.assertIn("Nordrhein-Westfalen, 32423 Minden", summary)
        self.assertIn("Kurz:", summary)
        self.assertIn("Mittelaltermarkt", summary)
        self.assertIn("Livemusik", summary)
        self.assertNotIn("http", summary)

    def test_news_links_are_discovered_from_source_page(self):
        html = """
        <a href="/aktuelles/neue-meldung">
          Eine wichtige neue Meldung mit genug Text im Linktitel
        </a>
        <a href="/kontakt">Kontakt</a>
        """

        candidates = extract_link_candidates(html, "https://example.org")

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["url"], "https://example.org/aktuelles/neue-meldung")
