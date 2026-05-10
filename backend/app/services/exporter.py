from __future__ import annotations

import csv
from io import StringIO

from app.core.signal_rules import get_config
from app.schemas import ClayExportRow, CompanyProfile, SignalScore


# ─── Formatting helpers ───────────────────────────────────────────────────────

def _format_signal_breakdown(signal_scores: list[SignalScore]) -> str:
    """Human-readable signal breakdown for the Clay export.

    Example: "integration language: 15/15; developer surface: 12/15; demoability: 7/10"
    Only includes signals with points > 0.
    """
    parts = [
        f"{s.signal.value.replace('_', ' ')}: {s.points}/{s.max_points}"
        for s in sorted(signal_scores, key=lambda s: s.points, reverse=True)
        if s.points > 0
    ]
    return "; ".join(parts)


def _format_scoring_explanation(profile: CompanyProfile) -> str:
    """One-sentence explanation of why a company received its score."""
    positive = [s for s in profile.signal_scores if s.points > 0]
    if not positive:
        return f"Score {profile.score}/100 ({profile.confidence.value} confidence). No strong signals found."

    strong = [s for s in positive if s.points >= s.max_points * 0.7]
    moderate = [s for s in positive if s.points < s.max_points * 0.7]

    parts = [f"Score {profile.score}/100 ({profile.confidence.value} confidence)."]
    if strong:
        names = ", ".join(s.signal.value.replace("_", " ") for s in strong)
        parts.append(f"Strong: {names}.")
    if moderate:
        names = ", ".join(s.signal.value.replace("_", " ") for s in moderate)
        parts.append(f"Moderate: {names}.")
    if profile.disqualification_reason:
        parts.append(f"Disqualifier: {profile.disqualification_reason}.")
    return " ".join(parts)


def _format_demo_concept(profile: CompanyProfile) -> str:
    """Title + hypothesis + first two steps, semicolon-separated."""
    if not profile.demo:
        return ""
    parts = [profile.demo.title]
    if profile.demo.hypothesis and profile.demo.hypothesis != profile.demo.title:
        parts.append(profile.demo.hypothesis)
    if profile.demo.steps:
        parts.extend(profile.demo.steps[:2])
    return " | ".join(parts)


def _collect_contact_titles(profile: CompanyProfile) -> list[str]:
    """Flat deduplicated list of all persona titles, primary first."""
    seen: set[str] = set()
    titles: list[str] = []
    ordered = [profile.primary_persona] + [
        p for p in profile.personas if p != profile.primary_persona
    ] if profile.primary_persona else profile.personas
    for persona in ordered:
        if persona is None:
            continue
        for title in persona.titles:
            if title not in seen:
                seen.add(title)
                titles.append(title)
    return titles


# ─── Row builder ─────────────────────────────────────────────────────────────

def to_clay_row(profile: CompanyProfile) -> ClayExportRow:
    cfg = get_config()
    primary = profile.primary_persona
    secondaries = [p for p in profile.personas if p != primary and p is not None]
    all_titles = _collect_contact_titles(profile)

    trigger = profile.competitive_triggers[0] if profile.competitive_triggers else None
    competitor_field = ""
    if trigger:
        competitor_field = f"{trigger.competitor} — {trigger.angle}"

    source_pages = "; ".join(profile.pages_fetched) if profile.pages_fetched else ""

    return ClayExportRow(
        # Identity
        company_name=profile.name,
        domain=profile.domain,
        website_url=profile.website_url,
        category=profile.category,
        inferred_category=profile.inferred_category or profile.category,
        category_confidence=profile.category_confidence.value if profile.category_confidence else "",
        company_summary=profile.company_summary,
        company_summary_source=profile.company_summary_source,
        # Scoring
        score=profile.score,
        scoring_rules_version=cfg.get("scoring_rules_version", ""),
        scoring_profile_name=cfg.get("scoring_profile_name", ""),
        scoring_explanation=_format_scoring_explanation(profile),
        signal_score_breakdown=_format_signal_breakdown(profile.signal_scores),
        # Evidence
        evidence_summary=profile.evidence_summary,
        integration_need_hypothesis=profile.integration_need_hypothesis,
        # Personas
        primary_persona=primary.persona.value if primary else "",
        secondary_personas="; ".join(p.persona.value for p in secondaries),
        suggested_contact_titles="; ".join(all_titles),
        clay_contact_search_titles="; ".join(all_titles[:4]),
        persona_reasoning=" | ".join(profile.persona_reasoning),
        # Competitive
        competitor_or_existing_stack_trigger=competitor_field,
        # Outreach
        demo_concept=_format_demo_concept(profile),
        suggested_email_subject=profile.outreach.subject if profile.outreach else "",
        suggested_email_body=profile.outreach.body if profile.outreach else "",
        # Provenance
        source_pages_scanned=source_pages,
        # Clay workflow
        review_status=profile.review_status,
    )


def filter_companies(profiles: list[CompanyProfile], status: str | None = None) -> list[CompanyProfile]:
    """Filter profiles by review_status. Pass status=None to keep all."""
    if not status:
        return list(profiles)
    return [p for p in profiles if p.review_status == status]


def companies_to_csv(profiles: list[CompanyProfile]) -> str:
    rows = [to_clay_row(profile).model_dump() for profile in profiles]
    output = StringIO()
    if not rows:
        return ""
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
