from __future__ import annotations

from app.core.signal_rules import get_competitor_aliases
from app.schemas import CompetitiveTrigger, Evidence, SignalName


def detect_competitor_name(keyword: str, snippet: str = "") -> str | None:
    haystack = f"{keyword} {snippet}".lower()
    for competitor, aliases in get_competitor_aliases().items():
        if any(alias in haystack for alias in aliases):
            return competitor
    return None


def find_competitive_triggers(evidence: list[Evidence]) -> list[CompetitiveTrigger]:
    grouped: dict[str, list[Evidence]] = {}
    for ev in evidence:
        if ev.signal != SignalName.competitor_presence:
            continue
        competitor = detect_competitor_name(ev.matched_keyword, ev.snippet)
        if not competitor:
            continue
        grouped.setdefault(competitor, []).append(ev)

    triggers: list[CompetitiveTrigger] = []
    for competitor, items in grouped.items():
        triggers.append(
            CompetitiveTrigger(
                competitor=competitor,
                evidence_ids=[item.id for item in items[:3]],
                angle=(
                    f"Competitive signal found for {competitor}. "
                    "They may already understand the integration space — focus the conversation on "
                    "coverage gaps, implementation speed, maintenance burden, and whether a "
                    "custom-built integration path solves problems the current vendor does not."
                ),
            )
        )
    return triggers
