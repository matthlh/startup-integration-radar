from app.core.domain import company_name_from_domain, normalize_domain, website_url


def test_normalize_domain():
    assert normalize_domain("https://www.monk.ai/product") == "monk.ai"
    assert normalize_domain("merge.dev") == "merge.dev"


def test_website_url():
    assert website_url("www.example.com") == "https://example.com"


def test_company_name_from_domain():
    assert company_name_from_domain("useparagon.com") == "Useparagon"
