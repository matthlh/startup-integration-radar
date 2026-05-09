from app.schemas import CompanyProfile, Confidence
from app.services.exporter import companies_to_csv


def test_clay_export_contains_expected_columns():
    profile = CompanyProfile(
        name="Example",
        domain="example.com",
        website_url="https://example.com",
        category="workflow automation",
        score=80,
        confidence=Confidence.high,
        integration_need_hypothesis="Likely needs CRM integrations.",
    )
    csv_text = companies_to_csv([profile])
    assert "company_name" in csv_text
    assert "integration_need_hypothesis" in csv_text
    assert "Example" in csv_text
