"""Exa search provider — used ONLY for company discovery, never for contact enrichment.

Exa pricing is metered per call. This provider is gated by two settings:
  - ENABLE_EXTERNAL_API_CALLS must be true
  - EXA_API_KEY must be set

If either is missing, `ExternalCallsDisabled` is raised before any HTTP call is
made so we never spend money silently.

API reference: https://docs.exa.ai/reference/search

The /search endpoint currently accepts:
  - query: natural-language string
  - numResults: int
  - type: "neural" | "keyword" | "auto"
  - contents.text.maxCharacters: int — optional snippet of each result's text

The response shape used here is `{"results": [{"url", "title", "text", ...}]}`.
If Exa changes either shape, update only this file — downstream code consumes
DiscoveryCandidate objects.
"""

from __future__ import annotations

import httpx

from app.config import get_settings
from app.schemas import DiscoveryCandidate


EXA_SEARCH_URL = "https://api.exa.ai/search"


class ExternalCallsDisabled(RuntimeError):
    """Raised when an external API call is attempted while gated off.

    The CLI catches this to surface a clear error and fall back to dry-run.
    """


async def discover_with_exa(query: str, limit: int = 25) -> list[DiscoveryCandidate]:
    """Call the Exa /search endpoint and map results to DiscoveryCandidate.

    Raises ExternalCallsDisabled if ENABLE_EXTERNAL_API_CALLS is false or EXA_API_KEY
    is missing — checked before any network I/O so we never spend money silently.
    """
    settings = get_settings()
    if not settings.enable_external_api_calls:
        raise ExternalCallsDisabled(
            "ENABLE_EXTERNAL_API_CALLS is false. Set it to true in .env to allow paid calls."
        )
    if not settings.exa_api_key:
        raise ExternalCallsDisabled(
            "EXA_API_KEY is missing. Add it to .env to enable live Exa discovery."
        )

    payload = {
        "query": query,
        "numResults": limit,
        "type": "auto",
        "contents": {"text": {"maxCharacters": 400}},
    }
    headers = {"x-api-key": settings.exa_api_key, "content-type": "application/json"}

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(EXA_SEARCH_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    candidates: list[DiscoveryCandidate] = []
    for result in data.get("results", []):
        url = result.get("url", "")
        domain = url.replace("https://", "").replace("http://", "").split("/")[0]
        if domain.startswith("www."):
            domain = domain[4:]
        if not domain:
            continue
        candidates.append(
            DiscoveryCandidate(
                name=result.get("title") or domain,
                domain=domain,
                url=url or f"https://{domain}",
                reason=(result.get("text") or "")[:300],
                source="exa",
            )
        )
    return candidates
