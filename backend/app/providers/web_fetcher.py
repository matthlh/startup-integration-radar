from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.config import get_settings
from app.core.domain import normalize_domain, website_url

PREFERRED_PATHS = [
    "",
    "/product",
    "/platform",
    "/solutions",
    "/customers",
    "/integrations",
    "/partners",
    "/marketplace",
    "/developers",
    "/docs",
    "/api",
    "/security",
    "/careers",
    "/jobs",
]


@dataclass
class FetchedPage:
    url: str
    title: str
    text: str


def _asset_text(soup: BeautifulSoup) -> str:
    """Collect logo/image/link labels that normal page text often loses.

    This is especially useful for competitive triggers where a page may only show
    a Merge.dev or Paragon logo image with alt text or a branded asset filename.
    """
    parts: list[str] = []
    for tag in soup.find_all(["img", "source"]):
        for attr in ["alt", "title", "aria-label", "src", "data-src"]:
            value = tag.get(attr)
            if value:
                parts.append(str(value))
    for tag in soup.find_all("a"):
        label = tag.get_text(" ", strip=True)
        href = tag.get("href")
        if label:
            parts.append(label)
        if href and any(token in href.lower() for token in ["merge", "paragon", "integrations", "partners", "marketplace"]):
            parts.append(href)
    return " ".join(parts)


def html_to_text(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    asset_text = _asset_text(soup)
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    text = soup.get_text(" ", strip=True)
    if asset_text:
        text = f"{text} Page assets and links: {asset_text}"
    text = re.sub(r"\s+", " ", text)
    return title, text[:35000]


async def fetch_page(url: str) -> FetchedPage | None:
    settings = get_settings()
    headers = {"User-Agent": settings.user_agent}
    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type and "application/xhtml" not in content_type:
                return None
            title, text = html_to_text(response.text)
            if len(text) < 100:
                return None
            return FetchedPage(url=str(response.url), title=title, text=text)
    except Exception:
        return None


async def fetch_company_pages(domain: str, max_pages: int = 10) -> list[FetchedPage]:
    domain = normalize_domain(domain)
    base = website_url(domain)
    pages: list[FetchedPage] = []
    seen: set[str] = set()

    for path in PREFERRED_PATHS:
        if len(pages) >= max_pages:
            break
        url = urljoin(base, path)
        if url in seen:
            continue
        seen.add(url)
        page = await fetch_page(url)
        if page:
            pages.append(page)

    return pages
