import csv
from io import StringIO

from app.schemas import (
    CompetitiveTrigger,
    CompanyProfile,
    Confidence,
    DemoConcept,
    OutreachAsset,
    PersonaName,
    PersonaRecommendation,
    SignalName,
    SignalScore,
)
from app.services.exporter import companies_to_csv


REQUIRED_COLUMNS = [
    "company_name",
    "domain",
    "website_url",
    "category",
    "inferred_category",
    "category_confidence",
    "company_summary",
    "company_summary_source",
    "score",
    "scoring_rules_version",
    "scoring_profile_name",
    "scoring_explanation",
    "signal_score_breakdown",
    "evidence_summary",
    "integration_need_hypothesis",
    "primary_persona",
    "secondary_personas",
    "suggested_contact_titles",
    "clay_contact_search_titles",
    "persona_reasoning",
    "competitor_or_existing_stack_trigger",
    "demo_concept",
    "suggested_email_subject",
    "suggested_email_body",
    "source_pages_scanned",
    "review_status",
    "notes",
]


def _rich_profile() -> CompanyProfile:
    primary = PersonaRecommendation(
        persona=PersonaName.product,
        titles=["Head of Product", "VP Product", "Product Lead", "Product Manager, Integrations"],
        why="Product owns roadmap tradeoffs.",
        priority=5,
    )
    secondary = PersonaRecommendation(
        persona=PersonaName.partnerships,
        titles=["Head of Partnerships", "Partnerships Lead", "Ecosystem Lead"],
        why="Partnerships owns ecosystem expansion.",
        priority=4,
    )
    engineering = PersonaRecommendation(
        persona=PersonaName.engineering,
        titles=["CTO", "Head of Engineering"],
        why="Engineering owns the maintenance cost.",
        priority=4,
    )
    return CompanyProfile(
        name="Example",
        domain="example.com",
        website_url="https://example.com",
        category="workflow automation",
        company_summary="Example builds workflow automation for B2B operations teams.",
        company_summary_source="meta_description",
        score=82,
        confidence=Confidence.high,
        integration_need_hypothesis="Likely needs CRM integrations.",
        evidence_summary="Mentioned 'Salesforce' and 'NetSuite' on their careers page.",
        signal_scores=[
            SignalScore(signal=SignalName.integration_language, points=15, max_points=15),
            SignalScore(signal=SignalName.developer_surface, points=12, max_points=15),
            SignalScore(signal=SignalName.demoability, points=7, max_points=10),
            SignalScore(signal=SignalName.partner_ecosystem, points=0, max_points=5),
        ],
        primary_persona=primary,
        personas=[primary, secondary, engineering],
        competitive_triggers=[
            CompetitiveTrigger(
                competitor="Merge.dev",
                angle="Comparison angle: position against Merge.dev rather than generic integration pitch.",
            )
        ],
        outreach=OutreachAsset(
            subject="Quick thought on Example's integrations",
            body="Hi — saw you mention Salesforce and NetSuite. Quick thought on closing those last-mile syncs.",
        ),
        demo=DemoConcept(
            title="Salesforce → Example workflow sync",
            hypothesis="Customers want one-click contact + activity sync.",
            steps=["Mock CSV import", "Render diff against Example UI", "Push to Salesforce sandbox"],
        ),
        pages_fetched=[
            "https://example.com/",
            "https://example.com/careers",
            "https://example.com/docs",
        ],
    )


def _row_dict(profile: CompanyProfile) -> dict:
    csv_text = companies_to_csv([profile])
    reader = csv.DictReader(StringIO(csv_text))
    rows = list(reader)
    assert len(rows) == 1
    return rows[0]


def test_clay_export_has_all_required_columns():
    profile = _rich_profile()
    csv_text = companies_to_csv([profile])
    header = csv_text.splitlines()[0]
    columns = [c.strip() for c in header.split(",")]
    for col in REQUIRED_COLUMNS:
        assert col in columns, f"missing column: {col}"


def test_clay_export_minimal_profile_still_renders():
    """A profile with no personas/outreach/demo/triggers should not crash and should still emit every column."""
    profile = CompanyProfile(
        name="Bare",
        domain="bare.com",
        website_url="https://bare.com",
        category="B2B workflow software",
        score=20,
        confidence=Confidence.low,
        integration_need_hypothesis="",
        evidence_summary="",
    )
    row = _row_dict(profile)
    for col in REQUIRED_COLUMNS:
        assert col in row
    assert row["primary_persona"] == ""
    assert row["secondary_personas"] == ""
    assert row["suggested_contact_titles"] == ""
    assert row["clay_contact_search_titles"] == ""
    assert row["competitor_or_existing_stack_trigger"] == ""
    assert row["suggested_email_body"] == ""
    assert row["demo_concept"] == ""
    assert row["review_status"] == "new"


def test_signal_score_breakdown_is_human_readable():
    row = _row_dict(_rich_profile())
    breakdown = row["signal_score_breakdown"]
    assert "{" not in breakdown and "}" not in breakdown
    assert "[" not in breakdown
    assert "integration language: 15/15" in breakdown
    assert "developer surface: 12/15" in breakdown
    assert "demoability: 7/10" in breakdown
    # Zero-point signals are excluded.
    assert "partner ecosystem" not in breakdown
    # Sorted by points descending.
    assert breakdown.index("integration language") < breakdown.index("demoability")


def test_clay_contact_search_titles_is_semicolon_list_capped_at_four():
    row = _row_dict(_rich_profile())
    titles = row["clay_contact_search_titles"]
    parts = [t.strip() for t in titles.split(";") if t.strip()]
    assert 1 <= len(parts) <= 4
    # Primary persona's first title should appear first.
    assert parts[0] == "Head of Product"


def test_suggested_contact_titles_includes_all_personas_deduped():
    row = _row_dict(_rich_profile())
    titles = [t.strip() for t in row["suggested_contact_titles"].split(";") if t.strip()]
    assert "Head of Product" in titles
    assert "Head of Partnerships" in titles
    assert "CTO" in titles
    assert len(titles) == len(set(titles))


def test_secondary_personas_excludes_primary():
    row = _row_dict(_rich_profile())
    assert row["primary_persona"] == "product"
    secondaries = [p.strip() for p in row["secondary_personas"].split(";") if p.strip()]
    assert "product" not in secondaries
    assert "partnerships" in secondaries
    assert "engineering" in secondaries


def test_source_pages_scanned_joins_pages_fetched():
    row = _row_dict(_rich_profile())
    assert row["source_pages_scanned"] == (
        "https://example.com/; https://example.com/careers; https://example.com/docs"
    )


def test_outreach_subject_and_body_round_trip():
    row = _row_dict(_rich_profile())
    assert row["suggested_email_subject"] == "Quick thought on Example's integrations"
    assert "Salesforce and NetSuite" in row["suggested_email_body"]


def test_competitor_trigger_includes_competitor_and_angle():
    row = _row_dict(_rich_profile())
    field = row["competitor_or_existing_stack_trigger"]
    assert "Merge.dev" in field
    assert "Comparison angle" in field


def test_company_summary_and_source_round_trip():
    row = _row_dict(_rich_profile())
    assert row["company_summary"] == "Example builds workflow automation for B2B operations teams."
    assert row["company_summary_source"] == "meta_description"


def test_scoring_metadata_stamped_from_signals_yaml():
    row = _row_dict(_rich_profile())
    # signals.yaml ships scoring_profile_name="Integration Scout v1", scoring_rules_version="1.0"
    assert row["scoring_profile_name"] == "Integration Scout v1"
    assert row["scoring_rules_version"] == "1.0"


def test_scoring_explanation_mentions_score_and_strong_signals():
    row = _row_dict(_rich_profile())
    explanation = row["scoring_explanation"]
    assert "82/100" in explanation
    assert "high confidence" in explanation
    assert "integration language" in explanation
