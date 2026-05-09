from __future__ import annotations

import httpx

from app.config import get_settings
from app.schemas import DiscoveryCandidate


class ExternalCallsDisabled(RuntimeError):
    pass


async def discover_with_exa(query: str, limit: int = 25) -> list[DiscoveryCandidate]:
    settings = get_settings()
    if not settings.enable_external_api_calls:
        raise ExternalCallsDisabled("External API calls are disabled. Set ENABLE_EXTERNAL_API_CALLS=true.")
    if not settings.exa_api_key:
        raise ExternalCallsDisabled("EXA_API_KEY is missing.")

    # This endpoint shape is intentionally isolated here so Claude Code can update it
    # if the provider SDK/API changes. The rest of the app depends only on DiscoveryCandidate.
    payload = {
        "query": query,
        "numResults": limit,
        "type": "auto",
        "contents": {"text": {"maxCharacters": 400}},
    }
    headers = {"x-api-key": settings.exa_api_key, "content-type": "application/json"}
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post("https://api.exa.ai/search", json=payload, headers=headers)
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
