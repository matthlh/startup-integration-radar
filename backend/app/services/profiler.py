from __future__ import annotations

import re

from app.core.domain import company_name_from_domain, normalize_domain, website_url
from app.core.scoring import score_evidence
from app.core.signal_rules import get_config
from app.core.signals import extract_evidence, summarize_evidence
from app.providers.web_fetcher import fetch_company_pages
from app.schemas import CompanyProfile, PipelineStage
from app.services.competitive import find_competitive_triggers
from app.services.outreach import choose_likely_systems, make_demo_concept, make_integration_hypothesis, make_outreach
from app.services.persona import recommend_personas, select_primary_persona


EMPLOYEE_PATTERNS = [
    re.compile(r"(?:team of|team size|company of|we are)\s+(?:about|around|over|more than|under|less than)?\s*(\d{1,5})\s+(?:people|employees|team members)", re.I),
    re.compile(r"(\d{1,5})\s*[-–]\s*(?:person|people|employee)\s+(?:team|company)", re.I),
    re.compile(r"(\d{1,5})\+\s+(?:employees|people|team members)", re.I),
]


def infer_category(text: str) -> str:
    """Infer company vertical from text.

    Should be called with homepage text only — docs and careers pages mention
    customer system names (e.g. Procore, Autodesk) that pollute the result.
    """
    lowered = text.lower()
    for entry in get_config().get("categories", []):
        if any(kw in lowered for kw in entry.get("keywords", [])):
            return entry["name"]
    if "ai" in lowered or "automation" in lowered:
        return "vertical AI / workflow automation"
    return "B2B workflow software"


def infer_one_liner(name: str, text: str) -> str:
    clean = " ".join(text.split())
    if len(clean) < 80:
        return f"I was looking at {name}'s product and the workflow it supports."
    return f"I was looking at {name} and noticed you help teams with {clean[:180].rstrip()}..."


def infer_employee_count_estimate(text: str) -> int | None:
    clean = " ".join(text.split())
    candidates: list[int] = []
    for pattern in EMPLOYEE_PATTERNS:
        for match in pattern.finditer(clean):
            try:
                value = int(match.group(1))
            except (TypeError, ValueError):
                continue
            if 1 <= value <= 10000:
                candidates.append(value)
    if candidates:
        return max(candidates)

    lowered = clean.lower()
    if any(phrase in lowered for phrase in ["seed stage", "pre-seed", "small team", "founding team"]):
        return 25
    if any(phrase in lowered for phrase in ["series b", "series c", "enterprise scale", "global team"]):
        return 100
    return None


async def profile_company(domain: str, use_llm: bool = False) -> CompanyProfile:
    normalized = normalize_domain(domain)
    pages = await fetch_company_pages(normalized)
    combined_text = "\n\n".join(page.text for page in pages)
    source_url = pages[0].url if pages else website_url(normalized)
    page_title = pages[0].title if pages else ""

    evidence = []
    for page in pages:
        evidence.extend(extract_evidence(page.text, source_url=page.url, page_title=page.title))
    if not evidence and combined_text:
        evidence = extract_evidence(combined_text, source_url=source_url, page_title=page_title)

    score, confidence, signal_scores, stage, disqualification_reason = score_evidence(evidence)
    name = company_name_from_domain(normalized)
    # Use homepage text only for category — docs and careers pages mention
    # customer system names that misattribute the company's vertical.
    homepage_text = pages[0].text if pages else combined_text
    category = infer_category(homepage_text)
    systems = choose_likely_systems(combined_text)
    employee_count_estimate = infer_employee_count_estimate(combined_text)

    profile = CompanyProfile(
        name=name,
        domain=normalized,
        website_url=website_url(normalized),
        one_liner=infer_one_liner(name, combined_text),
        category=category,
        customer_type="B2B teams using existing operational software",
        employee_count_estimate=employee_count_estimate,
        likely_customer_systems=systems,
        evidence=evidence,
        evidence_summary=summarize_evidence(evidence),
        competitive_triggers=find_competitive_triggers(evidence),
        signal_scores=signal_scores,
        score=score,
        confidence=confidence,
        stage=stage,
        disqualification_reason=disqualification_reason,
    )
    profile.integration_need_hypothesis = make_integration_hypothesis(profile)
    profile.primary_persona = select_primary_persona(employee_count_estimate)
    profile.personas = recommend_personas(signal_scores, score, employee_count_estimate)
    if score >= 55 and stage != PipelineStage.disqualified:
        profile.outreach = make_outreach(profile)
        profile.demo = await make_demo_concept(profile, use_llm=use_llm)
        profile.stage = PipelineStage.outbound_ready
    return profile
