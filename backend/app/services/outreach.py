from __future__ import annotations

from app.core.signal_rules import get_company_name
from app.providers.anthropic import LLMUnavailable, complete_json
from app.schemas import CompanyProfile, DemoConcept, OutreachAsset


def make_integration_hypothesis(profile: CompanyProfile) -> str:
    systems = profile.likely_customer_systems or ["customer systems", "CRMs", "internal operations tools"]
    system_text = ", ".join(systems[:3])
    category = profile.category or "workflow software"
    if profile.competitive_triggers:
        competitor = profile.competitive_triggers[0].competitor
        return (
            f"{profile.name} appears to sell {category} and may already understand unified integrations "
            f"because public evidence mentions {competitor}. The stronger angle is a comparison: "
            f"coverage, implementation speed, and customer-facing syncs into {system_text}."
        )
    return (
        f"{profile.name} appears to sell {category} where customers likely need data to move "
        f"between the product and {system_text}."
    )


def _outreach_first_line(profile: CompanyProfile, fallback: str) -> str:
    """Prefer company_summary (extracted from meta/OG/headings) over raw one-liners."""
    summary = (profile.company_summary or "").strip()
    if summary:
        return f"I was reading about {profile.name} — {summary}"
    return profile.one_liner or fallback


def make_outreach(profile: CompanyProfile) -> OutreachAsset:
    if profile.competitive_triggers:
        return make_competitive_outreach(profile)

    company = get_company_name()
    systems = profile.likely_customer_systems or ["their existing customer systems", "CRMs", "internal databases"]
    first_system = systems[0]
    first_line = _outreach_first_line(
        profile,
        fallback=f"I was looking at {profile.name}'s product and the workflow it supports.",
    )
    subject = f"Integration question for {profile.name}"
    body = f"""Hi {{{{first_name}}}},

{first_line}

I had a quick question: do customers ever ask to connect {profile.name} into systems like {', '.join(systems[:3])}?

The reason I ask is that we help software teams build and maintain customer-facing integrations when they become a blocker for onboarding, enterprise deals, or implementation bandwidth.

Based on the public product flow, I could imagine customers wanting:
- data from {profile.name} synced into {first_system}
- events routed into an internal workflow or CRM
- customer-specific reporting or automation without pulling core engineering off roadmap

Worth a quick conversation to compare notes on where integrations are slowing things down?
""".strip()
    return OutreachAsset(
        subject=subject,
        body=body,
        first_line=first_line,
        call_to_action="Worth a quick conversation to compare notes?",
        risk_notes=["Validate the exact customer systems before sending high-volume outreach."],
    )


def make_competitive_outreach(profile: CompanyProfile) -> OutreachAsset:
    company = get_company_name()
    trigger = profile.competitive_triggers[0]
    systems = profile.likely_customer_systems or ["CRM", "ERP", "customer operations tools"]
    first_line = _outreach_first_line(
        profile,
        fallback=f"I was looking at {profile.name}'s product and integration surface.",
    )
    subject = f"Integration angle for {profile.name}"
    body = f"""Hi {{{{first_name}}}},

{first_line}

I noticed a public signal around {trigger.competitor}, so I'm guessing your team may already be thinking seriously about embedded or customer-facing integrations.

Rather than a generic "do you need integrations?" note, I had a more specific question: are there customer-requested systems where coverage, implementation speed, or maintenance still creates friction?

A demo for {profile.name} could show:
- a customer record/event from {profile.name} normalized into {systems[0]}
- sync status, retries, and field mappings visible to the customer
- a path to launch more integrations without pulling core product engineers off roadmap

Worth comparing notes on where your current integration approach is working well versus where customers still ask for more?
""".strip()
    return OutreachAsset(
        subject=subject,
        body=body,
        first_line=first_line,
        call_to_action="Worth comparing notes on current integration gaps?",
        risk_notes=[trigger.risk_note, "Confirm competitor mention is not just incidental before sending."],
    )


async def make_demo_concept(profile: CompanyProfile, use_llm: bool = False) -> DemoConcept:
    if use_llm:
        try:
            return await make_demo_concept_with_llm(profile)
        except LLMUnavailable:
            pass
    return make_demo_concept_deterministic(profile)


async def make_demo_concept_with_llm(profile: CompanyProfile) -> DemoConcept:
    company = get_company_name()
    system = (
        f"You are a GTM engineer designing tiny Vercel demos for B2B integration prospects on behalf of {company}. "
        "Return strict JSON only. Do not invent private facts. Base the demo on public evidence and the supplied hypothesis."
    )
    user = {
        "company": profile.name,
        "category": profile.category,
        "one_liner": profile.one_liner,
        "integration_need_hypothesis": profile.integration_need_hypothesis,
        "likely_customer_systems": profile.likely_customer_systems,
        "evidence_summary": profile.evidence_summary,
        "competitive_triggers": [trigger.model_dump() for trigger in profile.competitive_triggers],
        "instructions": (
            "Create a concrete integration demo concept. The best answer should sound like: "
            "'Show them syncing automotive inspection data directly into an Insurance Claim dashboard.' "
            "Return keys: title, hypothesis, steps, public_assets_needed, estimated_build_minutes."
        ),
    }
    data = await complete_json(system=system, user=str(user), max_tokens=1000)
    return DemoConcept(
        title=str(data.get("title") or f"{profile.name} integration demo"),
        hypothesis=str(data.get("hypothesis") or profile.integration_need_hypothesis),
        steps=[str(step) for step in data.get("steps", [])][:6] or make_demo_concept_deterministic(profile).steps,
        public_assets_needed=[str(item) for item in data.get("public_assets_needed", [])][:6]
        or ["website copy", "public screenshots", "docs or sample API response if available"],
        estimated_build_minutes=int(data.get("estimated_build_minutes") or 120),
    )


def make_demo_concept_deterministic(profile: CompanyProfile) -> DemoConcept:
    systems = profile.likely_customer_systems or ["CRM", "internal ops dashboard", "data warehouse"]
    workflow_object = infer_workflow_object(profile)
    if profile.competitive_triggers:
        competitor = profile.competitive_triggers[0].competitor
        return DemoConcept(
            title=f"Integration comparison: {profile.name} → {systems[0]}",
            hypothesis=profile.integration_need_hypothesis or make_integration_hypothesis(profile),
            steps=[
                f"Trigger: customer data or a new {workflow_object} is created in {profile.name}.",
                f"Transform: map {profile.name} fields into the destination schema for {systems[0]}.",
                f"Sync: push the normalized record into {systems[0]} via a unified integration flow.",
                f"Compare: show where this flow reduces friction versus a {competitor}-style integration path.",
                "Notify: surface success/failure to the customer and internal owner.",
                "Audit: show logs, retries, and customer-visible field mapping controls.",
            ],
            public_assets_needed=["website copy", "public integration page", "public competitor/logo evidence"],
            estimated_build_minutes=150,
        )

    return DemoConcept(
        title=f"{profile.name} → {systems[0]} integration flow",
        hypothesis=profile.integration_need_hypothesis or make_integration_hypothesis(profile),
        steps=[
            f"Trigger: a new {workflow_object} is created in {profile.name}.",
            f"Transform: normalize fields into the destination schema for {systems[0]}.",
            f"Sync: create or update the matching object in {systems[0]}.",
            "Notify: send a Slack/email alert when the sync succeeds or fails.",
            "Audit: show logs, retry state, and customer-visible mapping controls.",
        ],
        public_assets_needed=["website copy", "public screenshots", "docs or sample API response if available"],
        estimated_build_minutes=120,
    )


def infer_workflow_object(profile: CompanyProfile) -> str:
    text = (profile.one_liner + " " + profile.integration_need_hypothesis + " " + profile.evidence_summary).lower()
    if "claim" in text:
        return "claim"
    if "inspection" in text:
        return "inspection report"
    if "lead" in text or "prospect" in text:
        return "lead"
    if "invoice" in text or "accounting" in text:
        return "invoice/customer record"
    if "ticket" in text or "case" in text:
        return "support case"
    return "record"


def choose_likely_systems(
    text: str,
    *,
    seed_category: str = "",
    inferred_category: str = "",
) -> list[str]:
    """Pick destination systems for a company, evidence-first.

    Thin wrapper around services.destinations.select_destination_systems so
    legacy callers (and the profiler) stay simple.
    """
    from app.services.destinations import select_destination_systems

    return select_destination_systems(
        text,
        seed_category=seed_category,
        inferred_category=inferred_category,
    )
