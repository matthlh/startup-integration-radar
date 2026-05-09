from __future__ import annotations

from app.schemas import CompetitiveTrigger, Evidence, SignalName

COMPETITOR_ALIASES = {
    "Merge.dev": ["merge.dev", "merge api", "merge unified api"],
    "Paragon": ["useparagon", "paragon", "paragon embedded", "paragon integration"],
}


def detect_competitor_name(keyword: str, snippet: str = "") -> str | None:
    haystack = f"{keyword} {snippet}".lower()
    for competitor, aliases in COMPETITOR_ALIASES.items():
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
                    f"Competitive trigger found for {competitor}. Lead with a Rutter comparison angle: "
                    "they may already understand unified integrations, so the conversation should focus on "
                    "coverage gaps, implementation speed, maintenance burden, and whether a Rutter-powered "
                    "demo can show a better customer-facing integration path."
                ),
            )
        )
    return triggers
