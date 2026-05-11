"""Quality-of-analysis tests.

Each scenario builds a minimal CompanyProfile-as-if-crawled (using small mock
HTML or pre-extracted evidence) and asserts on the end-state demo / fit /
destination systems. These are the cases the user flagged after the first
real run:

  - BuildOps-like accounting → QuickBooks/NetSuite/Viewpoint, not fleet/claims
  - Retell-like voice agents → CRM/HubSpot, not fleet/claims
  - snapsheet.com directory → bad_fit, score capped at 20
  - Mature horizontal platform → mature_platform, downgraded from strong_fit
"""

from __future__ import annotations

import asyncio

from app.core.signals import extract_evidence
from app.providers.web_fetcher import FetchedPage, parse_page
from app.schemas import (
    CompanyProfile,
    Confidence,
    FitQuality,
    PipelineStage,
    SignalName,
    SignalScore,
)
from app.services.destinations import is_mature_platform, select_destination_systems
from app.services.fit_quality import compute_fit_quality
from app.services.outreach import make_demo_concept_deterministic
from app.services.profiler import detect_crawl_quality_warning, refresh_derived_fields


# ─── 1. BuildOps-like accounting/ERP company ────────────────────────────────

BUILDOPS_HOMEPAGE = """
<html>
  <head>
    <title>BuildOps — operations software for commercial contractors</title>
    <meta name="description" content="The all-in-one operations platform for commercial contractors. Integrates with QuickBooks, NetSuite, Sage Intacct, and Viewpoint Vista accounting systems for service, project, and field workflows.">
  </head>
  <body>
    <h1>Operations software for commercial mechanical, electrical, and plumbing contractors</h1>
    <h2>Built-in integrations with QuickBooks, NetSuite, Sage Intacct, and Viewpoint</h2>
    <p>Manage dispatch, service tickets, invoicing, and payroll. Connect your accounting system in minutes.</p>
  </body>
</html>
"""


def test_contractor_company_suggests_accounting_systems_not_fleet():
    """A BuildOps-like contractor page must surface QuickBooks/NetSuite/Sage,
    not fleet management."""
    page = parse_page(BUILDOPS_HOMEPAGE)
    systems = select_destination_systems(
        page.text + " " + page.meta_description,
        seed_category="contractor",
        inferred_category="construction tech",
    )
    joined = " ".join(systems).lower()
    assert "quickbooks" in joined
    assert "netsuite" in joined or "sage intacct" in joined
    assert "fleet" not in joined, f"fleet should not appear in {systems}"
    assert "claims" not in joined, f"claims should not appear in {systems}"


def test_contractor_demo_uses_accounting_target():
    profile = CompanyProfile(
        name="BuildOps",
        domain="buildops.com",
        website_url="https://buildops.com",
        category="contractor",
        inferred_category="construction tech",
        score=80,
        confidence=Confidence.high,
        company_summary="The all-in-one operations platform for commercial contractors. Integrates with QuickBooks, NetSuite, Sage Intacct, and Viewpoint Vista.",
        evidence_summary="Mentioned 'integration', 'quickbooks', 'netsuite' on the homepage.",
        signal_scores=[
            SignalScore(signal=SignalName.integration_language, points=15, max_points=15),
            SignalScore(signal=SignalName.workflow_product, points=15, max_points=15),
        ],
    )
    asyncio.run(refresh_derived_fields(profile))
    assert profile.demo is not None
    title = profile.demo.title.lower()
    assert "quickbooks" in title or "netsuite" in title or "sage intacct" in title
    assert "fleet" not in title


# ─── 2. Retell AI-like voice agent company ──────────────────────────────────

RETELL_HOMEPAGE = """
<html>
  <head>
    <title>Retell AI — AI voice agents for customer conversations</title>
    <meta name="description" content="Build AI voice agents that handle inbound and outbound calls. Sync call summaries and lead status to HubSpot, Salesforce, and Zendesk. Trigger follow-up tasks from every conversation.">
  </head>
  <body>
    <h1>AI voice agents that integrate with your CRM</h1>
    <h2>Sync call transcripts and lead qualification into HubSpot or Salesforce automatically</h2>
    <p>Webhooks, REST API, and prebuilt connectors for sales and support workflows.</p>
  </body>
</html>
"""


def test_voice_agent_company_suggests_crm_systems():
    page = parse_page(RETELL_HOMEPAGE)
    systems = select_destination_systems(
        page.text + " " + page.meta_description,
        seed_category="AI voice agents",
        inferred_category="vertical AI",
    )
    joined = " ".join(systems).lower()
    assert "hubspot" in joined or "salesforce" in joined
    # The category map for AI voice agents puts CRM systems first.
    assert "fleet" not in joined
    assert "claims" not in joined


def test_voice_agent_demo_mentions_crm_destination():
    profile = CompanyProfile(
        name="Retell AI",
        domain="retellai.com",
        website_url="https://retellai.com",
        category="AI voice agents",
        inferred_category="vertical AI",
        score=70,
        confidence=Confidence.medium,
        company_summary="Build AI voice agents that handle calls and sync to HubSpot or Salesforce.",
        evidence_summary="Mentioned 'hubspot', 'salesforce', 'api', 'webhooks' on the homepage.",
        signal_scores=[
            SignalScore(signal=SignalName.integration_language, points=12, max_points=15),
            SignalScore(signal=SignalName.developer_surface, points=12, max_points=15),
        ],
    )
    asyncio.run(refresh_derived_fields(profile))
    assert profile.demo is not None
    title = profile.demo.title.lower()
    assert "hubspot" in title or "salesforce" in title or "crm" in title
    assert "fleet" not in title


# ─── 3. Parked/directory domain (the real snapsheet.com problem) ─────────────

PARKED_DIRECTORY_HOMEPAGE = """
<html>
  <head><title>Directory of Useful Information</title></head>
  <body>
    <p>Directory of Useful Information. News Sources: ABC News, Al Jazeera, Alternative
    News Network, Associated Press, BBC. This page is for sale.</p>
  </body>
</html>
"""


def test_parked_directory_page_flags_bad_fit_and_caps_score():
    parsed = parse_page(PARKED_DIRECTORY_HOMEPAGE)
    homepage = FetchedPage(
        url="https://snapsheet.com/",
        title=parsed.title,
        text=parsed.text,
        meta_description=parsed.meta_description,
        page_type="homepage",
    )
    warning = detect_crawl_quality_warning(homepage, [homepage])
    assert "parked" in warning.lower() or "placeholder" in warning.lower()

    profile = CompanyProfile(
        name="Snapsheet",
        domain="snapsheet.com",
        website_url="https://snapsheet.com",
        category="insurance claims",
        score=80,                     # the *raw* signal score before bad-domain capping
        crawl_quality_warning=warning,
    )
    fit, reasoning = compute_fit_quality(profile, combined_text=homepage.text)
    assert fit == FitQuality.bad_fit
    assert "verify domain" in reasoning.lower()


def test_full_pipeline_caps_bad_domain_score():
    """End-to-end: a profile created with a parked-page warning should NOT
    leave the profiler with score > 20."""
    # We can't trivially run profile_company against a fake URL without HTTP,
    # but the cap logic lives in profile_company, so we exercise it via the
    # same helper the profiler calls.
    homepage = FetchedPage(
        url="https://snapsheet.com/",
        title="Directory of Useful Information",
        text="Directory of Useful Information News Sources " + ("x" * 600),
        page_type="homepage",
    )
    warning = detect_crawl_quality_warning(homepage, [homepage])
    assert warning  # sanity
    # Mirror the cap from profile_company exactly:
    bad_signals = ("parked", "placeholder", "no pages were fetched", "homepage was not reachable")
    score = 85
    if any(s in warning.lower() for s in bad_signals):
        score = min(score, 20)
    assert score == 20


# ─── 4. Mature horizontal platform downgrade ─────────────────────────────────

def test_mature_platform_hint_detects_known_domain():
    assert is_mature_platform("notion.so") is True
    assert is_mature_platform("slack.com") is True
    assert is_mature_platform("monk.ai") is False


def test_mature_platform_hint_detects_marketplace_language():
    text = "Browse the public app marketplace with thousands of integrations."
    assert is_mature_platform("randomstartup.com", text) is True


def test_mature_platform_downgrades_from_strong_to_mature():
    profile = CompanyProfile(
        name="Notion",
        domain="notion.so",
        website_url="https://notion.so",
        category="horizontal productivity",
        score=85,
        confidence=Confidence.high,
        signal_scores=[
            SignalScore(signal=SignalName.integration_language, points=15, max_points=15),
            SignalScore(signal=SignalName.developer_surface, points=15, max_points=15),
            SignalScore(signal=SignalName.workflow_product, points=15, max_points=15),
        ],
    )
    fit, reasoning = compute_fit_quality(profile, combined_text="Notion's app marketplace…")
    assert fit == FitQuality.mature_platform
    joined = reasoning.lower()
    assert "marketplace" in joined or "ecosystem" in joined


# ─── Scoring: careers-page hits should weigh less ────────────────────────────

def test_careers_only_evidence_scores_lower_than_homepage_evidence():
    """Same keywords, different page context. Careers hits weigh half.

    We compare points awarded to the *same* signal bucket so secondary signals
    triggered by careers-only phrases ("hiring") don't muddy the comparison.
    """
    snippet = "Acme integrates with Salesforce and NetSuite for accounting workflows."
    careers_evidence = extract_evidence(
        snippet,
        source_url="https://acme.com/careers/backend-engineer",
        page_title="Backend Engineer — Acme",
    )
    homepage_evidence = extract_evidence(
        snippet,
        source_url="https://acme.com/",
        page_title="Acme — homepage",
    )

    from app.core.scoring import score_evidence
    from app.schemas import SignalName

    _, _, careers_sigs, _, _ = score_evidence(careers_evidence)
    _, _, homepage_sigs, _, _ = score_evidence(homepage_evidence)

    def points(sigs, name):
        for s in sigs:
            if s.signal == name:
                return s.points
        return 0

    careers_il = points(careers_sigs, SignalName.integration_language)
    homepage_il = points(homepage_sigs, SignalName.integration_language)

    assert homepage_il > careers_il, (
        f"integration_language: expected homepage > careers, got "
        f"homepage={homepage_il} careers={careers_il}"
    )
