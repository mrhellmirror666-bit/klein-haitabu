import ipaddress
import socket
from urllib.parse import urlparse



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
