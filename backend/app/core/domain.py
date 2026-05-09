from __future__ import annotations

import re
from urllib.parse import urlparse


def normalize_domain(raw: str) -> str:
    raw = raw.strip().lower()
    if not raw:
        return raw
    if "://" not in raw:
        raw = "https://" + raw
    parsed = urlparse(raw)
    host = parsed.netloc or parsed.path.split("/")[0]
    if host.startswith("www."):
        host = host[4:]
    return host.strip("/")


def company_name_from_domain(domain: str) -> str:
    base = normalize_domain(domain).split(".")[0]
    return re.sub(r"[-_]+", " ", base).title()


def website_url(domain: str) -> str:
    return f"https://{normalize_domain(domain)}"


def safe_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
