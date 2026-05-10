import textwrap
from pathlib import Path

import pytest

from app.services.csv_importer import SeedCompany, parse_seed_csv


def write_csv(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "test.csv"
    p.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    return p


# ─── Parsing correctness ──────────────────────────────────────────────────────

def test_parse_all_columns(tmp_path):
    path = write_csv(tmp_path, """
        company_name,domain,category,notes
        Monk,monk.ai,automotive,AI inspection platform
    """)
    results = parse_seed_csv(path)
    assert len(results) == 1
    c = results[0]
    assert c.domain == "monk.ai"
    assert c.company_name == "Monk"
    assert c.category == "automotive"
    assert c.notes == "AI inspection platform"


def test_parse_domain_only_column(tmp_path):
    """domain is the only required column — others should default to empty string."""
    path = write_csv(tmp_path, """
        domain
        monk.ai
        openspace.ai
    """)
    results = parse_seed_csv(path)
    assert len(results) == 2
    assert results[0].domain == "monk.ai"
    assert results[0].company_name == ""
    assert results[0].category == ""
    assert results[0].notes == ""


def test_normalizes_domains(tmp_path):
    """Domains with https://, http://, www. and trailing slashes are normalized."""
    path = write_csv(tmp_path, """
        domain
        https://www.monk.ai/
        http://openspace.ai
        www.samsara.com
    """)
    results = parse_seed_csv(path)
    assert [c.domain for c in results] == ["monk.ai", "openspace.ai", "samsara.com"]


def test_skips_empty_domain_rows(tmp_path):
    """Rows with no domain value are silently skipped."""
    path = write_csv(tmp_path, """
        company_name,domain,category,notes
        Valid Co,monk.ai,automotive,good row
        No Domain,,logistics,should be skipped
        ,   ,,also skipped
        Another,openspace.ai,,fine
    """)
    results = parse_seed_csv(path)
    assert len(results) == 2
    assert results[0].domain == "monk.ai"
    assert results[1].domain == "openspace.ai"


def test_skips_fully_empty_rows(tmp_path):
    """Blank lines in the CSV body are skipped."""
    path = write_csv(tmp_path, """
        domain,company_name
        monk.ai,Monk

        openspace.ai,OpenSpace
    """)
    results = parse_seed_csv(path)
    assert len(results) == 2


def test_empty_file_returns_empty_list(tmp_path):
    """A CSV with only headers and no data rows returns []."""
    path = write_csv(tmp_path, """
        company_name,domain,category,notes
    """)
    results = parse_seed_csv(path)
    assert results == []


def test_supports_legacy_column_names(tmp_path):
    """Supports 'name' for company_name and 'reason' for notes (old format)."""
    path = write_csv(tmp_path, """
        name,domain,reason
        Monk,monk.ai,Seed company
    """)
    results = parse_seed_csv(path)
    assert len(results) == 1
    assert results[0].company_name == "Monk"
    assert results[0].notes == "Seed company"


def test_missing_optional_fields_default_to_empty_string(tmp_path):
    """Missing optional columns are set to empty string, not None."""
    path = write_csv(tmp_path, """
        domain
        monk.ai
    """)
    results = parse_seed_csv(path)
    c = results[0]
    assert c.company_name == ""
    assert c.category == ""
    assert c.notes == ""
    assert isinstance(c.company_name, str)


def test_strips_whitespace_from_values(tmp_path):
    """Leading/trailing whitespace in cell values is stripped."""
    path = write_csv(tmp_path, """
        company_name,domain,category
          Monk  ,  monk.ai  ,  automotive
    """)
    results = parse_seed_csv(path)
    assert results[0].domain == "monk.ai"
    assert results[0].company_name == "Monk"
    assert results[0].category == "automotive"


# ─── Seed file smoke test ─────────────────────────────────────────────────────

def test_seed_csv_is_valid():
    """The checked-in seed_companies.csv parses without errors."""
    seed_path = Path(__file__).resolve().parents[1] / "data" / "seed_companies.csv"
    assert seed_path.exists(), "seed_companies.csv not found"
    results = parse_seed_csv(seed_path)
    assert len(results) >= 5, "Expected at least 5 seed companies"
    for c in results:
        assert c.domain, f"Empty domain in seed CSV row: {c}"
