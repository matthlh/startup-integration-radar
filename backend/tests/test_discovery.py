"""Tests for the discovery workflow: dry-run candidates and CSV seed handoff."""

import asyncio
import csv
from pathlib import Path

import pytest

from app.providers.exa import ExternalCallsDisabled, discover_with_exa
from app.services.csv_importer import parse_seed_csv
from app.services.discovery import FALLBACK_CANDIDATES, discover_candidates


def test_dry_run_returns_fallback_candidates():
    candidates = asyncio.run(discover_candidates("ignored query", limit=5, dry_run=True))
    assert len(candidates) == 5
    domains = {c.domain for c in candidates}
    # Should match the built-in fallback list, not call Exa.
    fallback_domains = {d for _, d, _ in FALLBACK_CANDIDATES}
    assert domains.issubset(fallback_domains)
    assert all(c.source == "fallback_seed" for c in candidates)


def test_dry_run_limit_caps_results():
    candidates = asyncio.run(discover_candidates("ignored", limit=3, dry_run=True))
    assert len(candidates) == 3


def test_exa_call_raises_when_external_calls_disabled(monkeypatch):
    """Default settings should refuse to call Exa even with --live."""
    # get_settings is lru_cached, but the default Settings() returns
    # enable_external_api_calls=False with no key — perfect for this test.
    with pytest.raises(ExternalCallsDisabled):
        asyncio.run(discover_with_exa("test", limit=5))


def test_exa_call_raises_when_key_missing(monkeypatch):
    """If external calls are enabled but the key is empty, refuse cleanly."""
    from app.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "enable_external_api_calls", True)
    monkeypatch.setattr(settings, "exa_api_key", "")

    with pytest.raises(ExternalCallsDisabled, match="EXA_API_KEY"):
        asyncio.run(discover_with_exa("test", limit=5))


# ─── Discovery → seed CSV handoff ────────────────────────────────────────────

def test_discovery_results_can_be_written_to_seed_csv_and_parsed_back(tmp_path: Path):
    """The CSV the `discover` CLI writes must be readable by analyze-csv."""
    from scripts.radar import _write_seed_csv

    candidates = asyncio.run(discover_candidates("ignored", limit=4, dry_run=True))
    seed_path = tmp_path / "discovered_seeds.csv"
    _write_seed_csv(candidates, seed_path)

    # File exists and contains the expected columns + rows.
    assert seed_path.exists()
    with seed_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 4
    assert set(rows[0].keys()) >= {"company_name", "domain", "category", "notes"}

    # parse_seed_csv must accept the same file (analyze-csv depends on this).
    seeds = parse_seed_csv(seed_path)
    assert len(seeds) == 4
    written_domains = {s.domain for s in seeds}
    expected_domains = {c.domain for c in candidates}
    assert written_domains == expected_domains


def test_write_seed_csv_handles_empty_candidate_list(tmp_path: Path):
    from scripts.radar import _write_seed_csv

    seed_path = tmp_path / "empty.csv"
    _write_seed_csv([], seed_path)
    assert seed_path.exists()
    with seed_path.open(encoding="utf-8") as fh:
        contents = fh.read()
    # Header row only.
    assert contents.startswith("company_name,domain,category,notes")
    assert len(contents.splitlines()) == 1
