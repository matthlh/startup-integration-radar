from __future__ import annotations

import csv
from io import StringIO

from app.schemas import ClayExportRow, CompanyProfile


def to_clay_row(profile: CompanyProfile) -> ClayExportRow:
    top_persona = profile.primary_persona or (profile.personas[0] if profile.personas else None)
    suggested_titles = ", ".join(top_persona.titles if top_persona else ["Head of Product", "Head of Partnerships", "CTO"])
    demo_title = profile.demo.title if profile.demo else ""
    trigger = profile.competitive_triggers[0] if profile.competitive_triggers else None
    return ClayExportRow(
        company_name=profile.name,
        domain=profile.domain,
        website=profile.website_url,
        category=profile.category,
        score=profile.score,
        confidence=profile.confidence.value if hasattr(profile.confidence, "value") else str(profile.confidence),
        employee_count_estimate=profile.employee_count_estimate,
        integration_need_hypothesis=profile.integration_need_hypothesis,
        evidence_summary=profile.evidence_summary,
        competitive_trigger=trigger.competitor if trigger else "",
        competitive_angle=trigger.angle if trigger else "",
        persona_priority_1=top_persona.persona.value if top_persona else "product",
        suggested_titles=suggested_titles,
        outreach_subject=profile.outreach.subject if profile.outreach else "",
        outreach_body=profile.outreach.body if profile.outreach else "",
        demo_concept=demo_title,
    )


def companies_to_csv(profiles: list[CompanyProfile]) -> str:
    rows = [to_clay_row(profile).model_dump() for profile in profiles]
    output = StringIO()
    if not rows:
        return ""
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
