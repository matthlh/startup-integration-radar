from __future__ import annotations

import json

import httpx

from app.config import get_settings


class LLMUnavailable(RuntimeError):
    pass


async def complete_json(system: str, user: str, max_tokens: int = 1800) -> dict:
    settings = get_settings()
    if not settings.enable_external_api_calls:
        raise LLMUnavailable("External API calls are disabled. Set ENABLE_EXTERNAL_API_CALLS=true.")
    if not settings.anthropic_api_key:
        raise LLMUnavailable("ANTHROPIC_API_KEY is missing.")

    payload = {
        "model": "claude-3-5-sonnet-latest",
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    headers = {
        "x-api-key": settings.anthropic_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    text = "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMUnavailable(f"Claude returned non-JSON output: {text[:300]}") from exc
