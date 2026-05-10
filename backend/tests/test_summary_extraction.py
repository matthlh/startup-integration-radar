"""Tests for deterministic company-summary extraction.

Covers HTML parsing (meta description, OpenGraph, headings, fallback) and the
summary-picker priority used by the profiler.
"""

from app.providers.web_fetcher import FetchedPage, parse_page
from app.services.outreach import _outreach_first_line
from app.services.profiler import select_company_summary


META_HTML = """
<html>
  <head>
    <title>Monk — AI for automotive</title>
    <meta name="description" content="Monk is the AI company building the future of vehicle inspection for dealers, fleets, and insurers worldwide.">
    <meta property="og:description" content="OG fallback description that should be ignored.">
  </head>
  <body>
    <h1>Inspect every vehicle, instantly</h1>
    <p>Some longer marketing copy that we do not want to use as a summary because it is generic and noisy.</p>
  </body>
</html>
"""


OG_ONLY_HTML = """
<html>
  <head>
    <title>OpenSpace</title>
    <meta property="og:title" content="OpenSpace — site documentation">
    <meta property="og:description" content="OpenSpace captures construction sites with 360° cameras and turns the footage into searchable visual records linked to project plans.">
  </head>
  <body>
    <h1>Capture every job site</h1>
  </body>
</html>
"""


HEADINGS_ONLY_HTML = """
<html>
  <head>
    <title>Acme Workflows</title>
  </head>
  <body>
    <h1>Workflow automation for healthcare operations</h1>
    <h2>Connect EHR systems, billing platforms, and patient CRMs without engineering bandwidth</h2>
    <p>Marketing copy below.</p>
  </body>
</html>
"""


CLEAN_TEXT_FALLBACK_HTML = """
<html>
  <head>
    <title>Bare</title>
  </head>
  <body>
    <p>Bare is the platform for orchestrating customer onboarding workflows across multiple operational systems and partner connectors all in one shared workspace built for B2B revenue teams.</p>
  </body>
</html>
"""


SHORT_META_HTML = """
<html>
  <head>
    <meta name="description" content="Too short.">
  </head>
  <body>
    <h1>Headline that is long enough to satisfy the minimum summary length threshold</h1>
  </body>
</html>
"""


# ─── Parser tests ────────────────────────────────────────────────────────────

def test_parse_page_extracts_meta_description():
    page = parse_page(META_HTML)
    assert page.meta_description.startswith("Monk is the AI company")
    assert "vehicle inspection" in page.meta_description


def test_parse_page_extracts_og_title_and_description():
    page = parse_page(OG_ONLY_HTML)
    assert page.og_title == "OpenSpace — site documentation"
    assert page.og_description.startswith("OpenSpace captures construction sites")


def test_parse_page_extracts_h1_and_h2():
    page = parse_page(HEADINGS_ONLY_HTML)
    assert page.h1 == ["Workflow automation for healthcare operations"]
    assert page.h2 == ["Connect EHR systems, billing platforms, and patient CRMs without engineering bandwidth"]


def test_parse_page_falls_back_to_clean_text_when_no_metadata():
    page = parse_page(CLEAN_TEXT_FALLBACK_HTML)
    assert page.meta_description == ""
    assert page.og_description == ""
    assert "Bare is the platform" in page.text


def test_parse_page_returns_empty_strings_for_missing_metadata():
    page = parse_page("<html><body><p>only body</p></body></html>")
    assert page.meta_description == ""
    assert page.og_title == ""
    assert page.og_description == ""
    assert page.h1 == []


# ─── Summary picker tests ────────────────────────────────────────────────────

def test_select_summary_prefers_meta_description():
    page = parse_page(META_HTML)
    summary, source = select_company_summary(page)
    assert source == "meta_description"
    assert summary.startswith("Monk is the AI company")
    # The OG description should not have won.
    assert "OG fallback" not in summary


def test_select_summary_falls_back_to_og_description():
    page = parse_page(OG_ONLY_HTML)
    summary, source = select_company_summary(page)
    assert source == "og_description"
    assert summary.startswith("OpenSpace captures construction sites")


def test_select_summary_falls_back_to_h1_h2():
    page = parse_page(HEADINGS_ONLY_HTML)
    summary, source = select_company_summary(page)
    assert source == "h1_h2"
    assert "Workflow automation for healthcare operations" in summary
    assert "EHR systems" in summary  # h2 joined in


def test_select_summary_falls_back_to_cleaned_text():
    page = parse_page(CLEAN_TEXT_FALLBACK_HTML)
    summary, source = select_company_summary(page)
    assert source == "cleaned_text"
    assert "Bare is the platform for orchestrating customer onboarding" in summary


def test_select_summary_skips_too_short_meta_and_uses_h1():
    page = parse_page(SHORT_META_HTML)
    summary, source = select_company_summary(page)
    assert source == "h1_h2"
    assert "long enough" in summary


def test_select_summary_returns_empty_when_no_homepage():
    summary, source = select_company_summary(None)
    assert summary == ""
    assert source == ""


# ─── Outreach first line uses summary ────────────────────────────────────────

def test_outreach_first_line_uses_company_summary_when_available():
    """The outreach helper must prefer profile.company_summary over the raw fallback."""
    from app.schemas import CompanyProfile

    profile = CompanyProfile(
        name="Monk",
        domain="monk.ai",
        website_url="https://monk.ai",
        company_summary="Monk is the AI company building the future of vehicle inspection.",
    )
    line = _outreach_first_line(profile, fallback="generic fallback")
    assert "Monk is the AI company" in line
    assert "generic fallback" not in line


def test_outreach_first_line_falls_back_when_no_summary():
    from app.schemas import CompanyProfile

    profile = CompanyProfile(
        name="Acme",
        domain="acme.com",
        website_url="https://acme.com",
        company_summary="",
        one_liner="",
    )
    line = _outreach_first_line(profile, fallback="my fallback line")
    assert line == "my fallback line"
