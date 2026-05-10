from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

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
    meta_description: str = ""
    og_title: str = ""
    og_description: str = ""
    h1: list[str] = field(default_factory=list)
    h2: list[str] = field(default_factory=list)
    page_type: str = "other"


def classify_page_type(url: str) -> str:
    """Classify a URL into one of: homepage, integrations, docs, careers, blog, other.

    Used to weight category inference (homepage dominates) and explain evidence sources.
    """
    if not url:
        return "other"
    path = urlparse(url).path.lower().rstrip("/")
    if path in ("", "/"):
        return "homepage"
    if any(seg in path for seg in ["/integrations", "/integration", "/marketplace", "/partners", "/ecosystem", "/apps", "/connectors"]):
        return "integrations"
    if any(seg in path for seg in ["/docs", "/developer", "/developers", "/api", "/webhooks", "/sdk", "/reference"]):
        return "docs"
    if any(seg in path for seg in ["/careers", "/jobs", "/job/", "/hiring"]):
        return "careers"
    if any(seg in path for seg in ["/blog", "/news", "/press", "/insights", "/articles"]):
        return "blog"
    return "other"


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


def _meta_content(soup: BeautifulSoup, *, name: str | None = None, prop: str | None = None) -> str:
    """Find a <meta> tag by name= or property= and return its content attr."""
    if name:
        tag = soup.find("meta", attrs={"name": lambda v: v and v.lower() == name.lower()})
        if tag and tag.get("content"):
            return str(tag["content"]).strip()
    if prop:
        tag = soup.find("meta", attrs={"property": lambda v: v and v.lower() == prop.lower()})
        if tag and tag.get("content"):
            return str(tag["content"]).strip()
    return ""


def _heading_texts(soup: BeautifulSoup, level: str, limit: int = 5) -> list[str]:
    out: list[str] = []
    for tag in soup.find_all(level):
        text = tag.get_text(" ", strip=True)
        if not text:
            continue
        text = re.sub(r"\s+", " ", text)
        if text not in out:
            out.append(text)
        if len(out) >= limit:
            break
    return out


def parse_page(html: str) -> FetchedPage:
    """Parse HTML into a FetchedPage with title, text, and metadata fields.

    Pure parsing — no network. Exposed for tests and reuse.
    """
    soup = BeautifulSoup(html, "html.parser")
    asset_text = _asset_text(soup)

    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    meta_description = _meta_content(soup, name="description")
    og_title = _meta_content(soup, prop="og:title")
    og_description = _meta_content(soup, prop="og:description")
    h1 = _heading_texts(soup, "h1")
    h2 = _heading_texts(soup, "h2")

    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
    if asset_text:
        text = f"{text} Page assets and links: {asset_text}"
    text = re.sub(r"\s+", " ", text)

    return FetchedPage(
        url="",
        title=title,
        text=text[:35000],
        meta_description=meta_description,
        og_title=og_title,
        og_description=og_description,
        h1=h1,
        h2=h2,
    )


def html_to_text(html: str) -> tuple[str, str]:
    """Backward-compatible accessor: return (title, text).

    Newer code should call parse_page() to get the full metadata.
    """
    page = parse_page(html)
    return page.title, page.text


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
            page = parse_page(response.text)
            if len(page.text) < 100:
                return None
            page.url = str(response.url)
            page.page_type = classify_page_type(page.url)
            return page
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
