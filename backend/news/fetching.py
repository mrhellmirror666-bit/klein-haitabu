from urllib.request import Request, urlopen



MAX_DOWNLOAD_BYTES = 250_000
REQUEST_TIMEOUT_SECONDS = 8



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
