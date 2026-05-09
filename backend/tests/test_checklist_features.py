from app.core.signals import extract_evidence, summarize_evidence
from app.schemas import CompanyProfile, Confidence, Evidence, EvidenceType, SignalName
from app.services.competitive import find_competitive_triggers
from app.services.outreach import make_demo_concept_deterministic, make_integration_hypothesis, make_outreach
from app.services.persona import recommend_personas, select_primary_persona


def test_evidence_summary_mentions_keywords_and_source_context():
    text = """
    Senior Backend Engineer - Integrations. You will build NetSuite and QuickBooks syncs,
    maintain webhooks, and support enterprise accounting customers.
    """
    evidence = extract_evidence(text, source_url="https://example.com/careers/senior-backend-engineer")
    summary = summarize_evidence(evidence)
    assert "Mentioned" in summary
    assert "NetSuite" in summary or "netsuite" in summary.lower()
    assert "QuickBooks" in summary or "quickbooks" in summary.lower()
    assert "engineering job posting" in summary


def test_persona_logic_uses_founder_under_50_and_product_over_50():
    assert select_primary_persona(25).persona.value == "founder"
    assert select_primary_persona(75).persona.value == "product"

    small = recommend_personas([], score=65, employee_count_estimate=12)
    large = recommend_personas([], score=65, employee_count_estimate=120)

    assert small[0].persona.value == "founder"
    assert large[0].persona.value == "product"
    assert any(persona.persona.value == "partnerships" for persona in large)


def test_competitive_trigger_changes_hypothesis_outreach_and_demo():
    evidence = [
        Evidence(
            type=EvidenceType.integrations_page,
            snippet="Integration marketplace includes Paragon embedded integrations.",
            signal=SignalName.competitor_presence,
            weight=5,
            matched_keyword="Paragon",
            source_context="integrations/partners page",
        )
    ]
    triggers = find_competitive_triggers(evidence)
    profile = CompanyProfile(
        name="AcmeOps",
        domain="acmeops.com",
        website_url="https://acmeops.com",
        category="vertical AI / workflow automation",
        likely_customer_systems=["Salesforce", "NetSuite"],
        evidence=evidence,
        evidence_summary=summarize_evidence(evidence),
        competitive_triggers=triggers,
        score=82,
        confidence=Confidence.high,
    )
    profile.integration_need_hypothesis = make_integration_hypothesis(profile)
    outreach = make_outreach(profile)
    demo = make_demo_concept_deterministic(profile)

    assert triggers[0].competitor == "Paragon"
    assert "comparison" in profile.integration_need_hypothesis
    assert "Paragon" in outreach.body
    assert "comparison" in demo.title.lower()
