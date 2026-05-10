"""Tests for review_status filtering on the Clay export."""

import csv
from io import StringIO

from app.schemas import CompanyProfile
from app.services.exporter import companies_to_csv, filter_companies


def _profile(domain: str, status: str = "new") -> CompanyProfile:
    return CompanyProfile(
        name=domain.split(".")[0].title(),
        domain=domain,
        website_url=f"https://{domain}",
        category="B2B workflow software",
        review_status=status,
    )


def _domains_in_csv(csv_text: str) -> list[str]:
    if not csv_text.strip():
        return []
    reader = csv.DictReader(StringIO(csv_text))
    return [row["domain"] for row in reader]


# ─── filter_companies ────────────────────────────────────────────────────────

def test_filter_none_returns_all():
    profiles = [_profile("a.com", "new"), _profile("b.com", "approved"), _profile("c.com", "skip")]
    assert filter_companies(profiles, status=None) == profiles


def test_filter_empty_string_returns_all():
    profiles = [_profile("a.com", "new"), _profile("b.com", "approved")]
    # Empty string should behave like None — no filter.
    assert filter_companies(profiles, status="") == profiles


def test_filter_approved_drops_new_and_skip():
    profiles = [
        _profile("approved-1.com", "approved"),
        _profile("new-1.com", "new"),
        _profile("skip-1.com", "skip"),
        _profile("approved-2.com", "approved"),
    ]
    filtered = filter_companies(profiles, status="approved")
    assert [p.domain for p in filtered] == ["approved-1.com", "approved-2.com"]


def test_filter_skip_returns_only_skip():
    profiles = [
        _profile("a.com", "new"),
        _profile("b.com", "approved"),
        _profile("c.com", "skip"),
    ]
    filtered = filter_companies(profiles, status="skip")
    assert [p.domain for p in filtered] == ["c.com"]


def test_filter_unknown_status_returns_empty():
    profiles = [_profile("a.com", "new"), _profile("b.com", "approved")]
    assert filter_companies(profiles, status="unrecognized") == []


# ─── End-to-end: filter + CSV export ─────────────────────────────────────────

def test_csv_export_default_includes_every_status():
    profiles = [
        _profile("approved-1.com", "approved"),
        _profile("new-1.com", "new"),
        _profile("skip-1.com", "skip"),
    ]
    csv_text = companies_to_csv(profiles)
    domains = _domains_in_csv(csv_text)
    assert set(domains) == {"approved-1.com", "new-1.com", "skip-1.com"}


def test_csv_export_filtered_by_approved():
    profiles = [
        _profile("approved-1.com", "approved"),
        _profile("new-1.com", "new"),
        _profile("skip-1.com", "skip"),
        _profile("approved-2.com", "approved"),
    ]
    csv_text = companies_to_csv(filter_companies(profiles, status="approved"))
    domains = _domains_in_csv(csv_text)
    assert set(domains) == {"approved-1.com", "approved-2.com"}


def test_csv_export_filtered_to_zero_returns_empty_string():
    profiles = [_profile("a.com", "new")]
    csv_text = companies_to_csv(filter_companies(profiles, status="approved"))
    assert csv_text == ""


def test_csv_review_status_column_reflects_profile_value():
    profiles = [
        _profile("approved-1.com", "approved"),
        _profile("new-1.com", "new"),
    ]
    csv_text = companies_to_csv(profiles)
    rows = list(csv.DictReader(StringIO(csv_text)))
    by_domain = {row["domain"]: row["review_status"] for row in rows}
    assert by_domain["approved-1.com"] == "approved"
    assert by_domain["new-1.com"] == "new"
