import re
from datetime import datetime, timezone as datetime_timezone


def parse_german_date_from_text(text) -> datetime | None:
    numeric_match = re.search(r"\b(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{2,4})\b", text)
    if numeric_match:
        day, month, year = numeric_match.groups()
        year = normalize_year(year)
        hour, minute = parse_time_from_text(text)
        return datetime(int(year), int(month), int(day), hour, minute, tzinfo=datetime_timezone.utc)

    word_match = re.search(
        r"\b(\d{1,2})\.\s*(Januar|Februar|Maerz|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+(\d{4})\b",
        text,
        flags=re.IGNORECASE,
    )
    if word_match:
        day, month_name, year = word_match.groups()
        hour, minute = parse_time_from_text(text)
        return datetime(int(year), month_number(month_name), int(day), hour, minute, tzinfo=datetime_timezone.utc)

    return None


def parse_time_from_text(text) -> tuple[int, int]:
    match = re.search(r"\b(\d{1,2}):(\d{2})\b", text)
    if match:
        return int(match.group(1)), int(match.group(2))

    match = re.search(r"\b(\d{1,2})\.(\d{2})\s*Uhr\b", text, flags=re.IGNORECASE)
    if not match:
        return 0, 0
    return int(match.group(1)), int(match.group(2))


def normalize_year(year: str) -> str:
    if len(year) == 2:
        return f"20{year}"
    return year


def month_number(month_name: str) -> int:
    normalized = month_name.lower().replace("ä", "ae")
    months = {
        "januar": 1,
        "februar": 2,
        "maerz": 3,
        "april": 4,
        "mai": 5,
        "juni": 6,
        "juli": 7,
        "august": 8,
        "september": 9,
        "oktober": 10,
        "november": 11,
        "dezember": 12,
    }
    return months[normalized]
