"""Tests for page-type-weighted category inference.

Pollution scenario: an integrations company whose careers page lists Procore /
Autodesk should NOT be tagged as construction tech. The homepage should win.
"""

from app.core.signals import extract_evidence
from app.providers.web_fetcher import FetchedPage, classify_page_type, parse_page
from app.services.profiler import infer_category_weighted


def _homepage(html: str, url: str = "https://acme.com/") -> FetchedPage:
    page = parse_page(html)
    page.url = url
    page.page_type = classify_page_type(url)
    return page


def _careers_page(text: str, url: str = "https://acme.com/careers/backend-engineer") -> FetchedPage:
    return FetchedPage(
        url=url,
        title="Careers",
        text=text,
        page_type=classify_page_type(url),
    )


def _docs_page(text: str, url: str = "https://acme.com/docs/api") -> FetchedPage:
    return FetchedPage(
        url=url,
        title="API Docs",
        text=text,
        page_type=classify_page_type(url),
    )


# ─── Page type classifier ────────────────────────────────────────────────────

def test_classify_page_type():
    assert classify_page_type("https://acme.com/") == "homepage"
    assert classify_page_type("https://acme.com") == "homepage"
    assert classify_page_type("https://acme.com/integrations") == "integrations"
    assert classify_page_type("https://acme.com/marketplace/foo") == "integrations"
    assert classify_page_type("https://acme.com/docs/api/webhooks") == "docs"
    assert classify_page_type("https://acme.com/api") == "docs"
    assert classify_page_type("https://acme.com/careers/backend") == "careers"
    assert classify_page_type("https://acme.com/jobs/123") == "careers"
    assert classify_page_type("https://acme.com/blog/launch-day") == "blog"
    assert classify_page_type("https://acme.com/about") == "other"


# ─── Category inference ──────────────────────────────────────────────────────

SALES_AUTOMATION_HOMEPAGE = """
<html>
  <head>
    <title>SellFast — sales automation platform for outbound teams</title>
    <meta name="description" content="SellFast is a sales engagement platform that helps outbound sales teams automate prospect outreach and pipeline workflows.">
  </head>
  <body>
    <h1>Sales engagement, automated</h1>
    <h2>Built for outbound sales teams who need pipeline velocity</h2>
    <p>SellFast helps sales teams reach more prospects with automated sequences.</p>
  </body>
</html>
"""


def test_homepage_category_wins_over_careers_keywords():
    """An integrations/sales company whose careers page mentions Procore + Autodesk
    must not get tagged as construction tech."""
    homepage = _homepage(SALES_AUTOMATION_HOMEPAGE)
    careers = _careers_page(
        "We are hiring a Senior Backend Engineer to build integrations with "
        "Procore, Autodesk Construction Cloud, and other construction project "
        "management systems used by our customers."
    )

    inferred, confidence, evidence = infer_category_weighted(homepage, [careers])

    assert inferred == "sales automation"
    assert confidence in ("medium", "high")
    # Evidence should reference homepage signals first.
    assert any("homepage" in line for line in evidence)


def test_integration_evidence_still_extracted_from_careers_page():
    """Even if careers-page keywords don't dominate the category, integration
    evidence must still be picked up by the signal extractor."""
    careers_text = (
        "Senior Backend Engineer - Integrations. You will build NetSuite and "
        "QuickBooks syncs, maintain webhooks, and support enterprise accounting customers."
    )
    careers_evidence = extract_evidence(
        careers_text,
        source_url="https://acme.com/careers/backend-engineer",
    )
    keywords = {ev.matched_keyword.lower() for ev in careers_evidence}
    # Integration signals from the careers page must still register for scoring.
    assert "netsuite" in keywords
    assert "quickbooks" in keywords or "webhooks" in keywords


def test_unknown_category_falls_back_with_low_confidence():
    """A homepage with no category keywords lands on the default fallback."""
    homepage = _homepage(
        """
        <html>
          <head>
            <title>Foobar</title>
            <meta name="description" content="A new kind of tool for teams who want to do things together.">
          </head>
          <body>
            <h1>Foobar makes work easier</h1>
            <p>We help teams collaborate.</p>
          </body>
        </html>
        """
    )
    inferred, confidence, evidence = infer_category_weighted(homepage, [])
    # Falls through to one of the two defaults — neither matches signals.yaml verticals.
    assert inferred in ("vertical AI / workflow automation", "B2B workflow software")
    assert confidence == "low"
    assert evidence == []


def test_unknown_category_with_ai_keyword_routes_to_vertical_ai():
    homepage = _homepage(
        """
        <html>
          <head><title>Foobar</title>
          <meta name="description" content="An AI platform for teams."></head>
          <body><h1>AI-powered workflows for teams</h1></body>
        </html>
        """
    )
    inferred, confidence, evidence = infer_category_weighted(homepage, [])
    # No signals.yaml category keyword matches, so it falls to the AI/automation default.
    assert inferred == "vertical AI / workflow automation"
    assert confidence == "low"


def test_no_homepage_returns_default():
    inferred, confidence, evidence = infer_category_weighted(None, [])
    assert inferred == "B2B workflow software"
    assert confidence == "low"
    assert evidence == []


def test_strong_homepage_signals_yield_high_confidence():
    """A homepage with multiple matching keywords across title, meta, and h1 should
    push the confidence to 'high' rather than 'medium'."""
    html = """
    <html>
      <head>
        <title>BuildIt — construction tech for general contractors</title>
        <meta name="description" content="BuildIt is construction project management software for general contractors and subcontractors who need BIM-aware workflows.">
      </head>
      <body>
        <h1>Construction project management</h1>
        <h2>Built for contractors and subcontractors</h2>
        <p>Construction teams use BuildIt to coordinate field work.</p>
      </body>
    </html>
    """
    homepage = _homepage(html, url="https://buildit.com/")
    inferred, confidence, evidence = infer_category_weighted(homepage, [])
    assert inferred == "construction tech"
    assert confidence == "high"
