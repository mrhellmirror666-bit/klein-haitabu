from datetime import datetime, timezone

from django.test import TestCase

from common.dates import parse_german_date_from_text, parse_time_from_text


class DateParsingTests(TestCase):
    def test_numeric_german_date_is_parsed(self):
        parsed = parse_german_date_from_text("Termin am 15.03.2025")

        self.assertEqual(parsed, datetime(2025, 3, 15, tzinfo=timezone.utc))

    def test_written_german_month_is_parsed(self):
        parsed = parse_german_date_from_text("Termin am 3. März 2025")

        self.assertEqual(parsed, datetime(2025, 3, 3, tzinfo=timezone.utc))

    def test_time_is_parsed(self):
        parsed = parse_time_from_text("Beginn 19:30 Uhr")

        self.assertEqual(parsed, (19, 30))

    def test_text_without_date_returns_none(self):
        parsed = parse_german_date_from_text("Kein Termin in diesem Text")

        self.assertIsNone(parsed)
