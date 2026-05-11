"""Evidence-first selection of destination systems.

Replaces the old `choose_likely_systems` keyword tuple, which picked the first
matching category (so a contractor page mentioning "field" got tagged as
automotive → fleet management).

Order of preference:
  1. Branded systems found verbatim in the crawled text (HubSpot, Salesforce,
     QuickBooks, NetSuite, Procore, Viewpoint, ...).
  2. Category-specific defaults from `destination_systems` in signals.yaml,
     keyed first on the seed-CSV category, then the inferred homepage category.
  3. Generic CRM / ERP / database fallback.
"""

from __future__ import annotations

from typing import Iterable

from app.core.signal_rules import get_config


_DEFAULT_FALLBACK = ["CRM", "ERP", "internal operations database"]


def _known_systems_in_text(text: str) -> list[str]:
    """Return canonical display names for any branded systems mentioned in text."""
    if not text:
        return []
    lowered = text.lower()
    config = get_config().get("known_systems", {}) or {}
    found: list[str] = []
    for display_name, aliases in config.items():
        for alias in aliases or []:
            if alias.lower() in lowered and display_name not in found:
                found.append(display_name)
                break
    return found


def _systems_for_category(category: str) -> list[str]:
    table = get_config().get("destination_systems", {}) or {}
    if not category:
        return []
    # Exact match first, then case-insensitive match.
    if category in table:
        return list(table[category])
    lowered = category.lower().strip()
    for key, value in table.items():
        if key.lower() == lowered:
            return list(value)
    return []


def _dedupe(items: Iterable[str], limit: int = 6) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if not item:
            continue
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
        if len(out) >= limit:
            break
    return out


def select_destination_systems(
    text: str,
    *,
    seed_category: str = "",
    inferred_category: str = "",
    limit: int = 4,
) -> list[str]:
    """Pick destination systems for outreach + demo, preferring evidence.

    Args:
        text: combined crawled text (homepage + secondary pages).
        seed_category: category the operator typed in the seed CSV. Takes
            precedence over inferred_category because the operator usually
            knows the company better than the regex.
        inferred_category: category derived from the homepage signals.
        limit: cap on returned systems.
    """
    branded = _known_systems_in_text(text)

    category_default = (
        _systems_for_category(seed_category)
        or _systems_for_category(inferred_category)
        or list(get_config().get("destination_systems", {}).get("default", _DEFAULT_FALLBACK))
    )

    # Branded findings first, padded by the category default.
    return _dedupe(branded + category_default, limit=limit)


def is_mature_platform(profile_domain: str, text: str = "") -> bool:
    """True when a domain or its crawled copy reads like Notion / Slack / etc.

    Mature horizontal platforms already have huge integration ecosystems and
    aren't great targets for a build-and-maintain integrations pitch — so we
    flag them so the fit_quality computation can downgrade strong_fit to
    mature_platform.
    """
    cfg = get_config().get("mature_platform_hints", {}) or {}
    domains = [d.lower() for d in cfg.get("domains", []) or []]
    keywords = [k.lower() for k in cfg.get("keywords", []) or []]

    if profile_domain and profile_domain.lower() in domains:
        return True
    if text and any(kw in text.lower() for kw in keywords):
        return True
    return False
