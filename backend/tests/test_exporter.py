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
        evidence_summary="Mentioned 'Salesforce' and 'NetSuite' on their careers page.",
    )
    csv_text = companies_to_csv([profile])
    assert "company_name" in csv_text
    assert "integration_need_hypothesis" in csv_text
    assert "evidence_summary" in csv_text
    assert "Example" in csv_text
    assert "Salesforce" in csv_text
