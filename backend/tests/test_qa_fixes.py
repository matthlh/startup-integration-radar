"""Regression tests for the QA-report bug fixes."""

import asyncio

from app.providers.web_fetcher import FetchedPage
from app.schemas import CompanyProfile, OutreachAsset, PipelineStage
from app.services.profiler import (
    detect_crawl_quality_warning,
    infer_employee_count_estimate,
    refresh_derived_fields,
)


# ─── Bug #3: employee count heuristic should not over-fire on "founding" ─────

def test_employee_heuristic_ignores_incidental_founding_word():
    """Tractable's homepage mentions 'since their founding' — must NOT flag as small."""
    text = (
        "Tractable was founded to bring AI to industries that move physical assets. "
        "Since their founding the team has grown across London, New York, and Tokyo."
    )
    assert infer_employee_count_estimate(text) is None


def test_employee_heuristic_still_catches_explicit_small_team():
    text = "We are a small team of seven engineers shipping every day."
    assert infer_employee_count_estimate(text) == 25


def test_employee_heuristic_catches_explicit_large_company():
    text = "Series B fintech with offices across three continents."
    assert infer_employee_count_estimate(text) == 100


def test_employee_heuristic_prefers_explicit_count_over_phrase():
    text = "Our team of 250 employees ships globally; series b raised last year."
    assert infer_employee_count_estimate(text) == 250


# ─── Bug #2: junk/parked homepages should produce a warning ─────────────────

def _page(text: str = "", title: str = "", meta: str = "", url: str = "https://x.com/", page_type: str = "homepage") -> FetchedPage:
    return FetchedPage(
        url=url,
        title=title,
        text=text,
        meta_description=meta,
        page_type=page_type,
    )


def test_crawl_warning_when_no_pages_fetched():
    warning = detect_crawl_quality_warning(None, [])
    assert "No pages were fetched" in warning


def test_crawl_warning_for_parked_domain_phrase():
    homepage = _page(
        text="Directory of Useful Information News Sources ABC News Al Jazeera",
        title="Directory of Useful Information",
    )
    warning = detect_crawl_quality_warning(homepage, [homepage])
    assert "parked" in warning.lower() or "placeholder" in warning.lower()


def test_crawl_warning_for_thin_homepage_text():
    homepage = _page(text="Welcome to our site. Coming soon.")
    warning = detect_crawl_quality_warning(homepage, [homepage])
    assert "very little text" in warning


def test_crawl_warning_for_homepage_only_when_secondary_pages_failed():
    homepage = _page(text="A" * 1000)  # plenty of text, just one page
    warning = detect_crawl_quality_warning(homepage, [homepage])
    assert "secondary pages" in warning


def test_no_crawl_warning_when_crawl_looks_healthy():
    homepage = _page(text="A" * 1000)
    docs = _page(url="https://x.com/docs", text="API docs", page_type="docs")
    warning = detect_crawl_quality_warning(homepage, [homepage, docs])
    assert warning == ""


# ─── Bug #1: hypothesis should reflect seed-CSV category override ──────────

def test_refresh_derived_fields_rebuilds_hypothesis_after_category_override():
    profile = CompanyProfile(
        name="Snapsheet",
        domain="snapsheet.com",
        website_url="https://snapsheet.com",
        category="finance operations",   # what the inference produced (wrong)
        score=70,
        likely_customer_systems=["NetSuite", "QuickBooks", "ERP"],
        integration_need_hypothesis="Snapsheet appears to sell finance operations …",
        outreach=OutreachAsset(subject="Subj", body="Body", first_line="line"),
    )
    # Operator overrides the category to the correct vertical.
    profile.category = "insurance claims"
    asyncio.run(refresh_derived_fields(profile, use_llm=False))
    assert "insurance claims" in profile.integration_need_hypothesis
    # Below-threshold scores still skip outreach generation, so guard that path:
    profile.score = 40
    profile.stage = PipelineStage.profiled
    asyncio.run(refresh_derived_fields(profile, use_llm=False))
    # Hypothesis is updated regardless of score.
    assert "insurance claims" in profile.integration_need_hypothesis
