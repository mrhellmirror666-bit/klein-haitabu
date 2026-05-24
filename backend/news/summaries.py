import re

from .parsing import (
    clean_title,
    extract_date_text,
    extract_event_keywords,
    extract_german_state,
    extract_opening_or_time_text,
    extract_postcode_place,
    strip_calendar_noise,
    strip_urls,
)



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

def remove_repeated_title(text, title):
    normalized_title = re.escape(title.strip())
    return re.sub(rf"^\s*{normalized_title}\s*", "", text, flags=re.IGNORECASE).strip()

def make_short_summary(text):
    text = strip_urls(text)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    useful_sentences = [sentence.strip() for sentence in sentences if len(sentence.strip()) > 60]
    summary = " ".join(useful_sentences[:2])
    if not summary and len(text) > 60:
        summary = text.strip()
    return summary[:900]
