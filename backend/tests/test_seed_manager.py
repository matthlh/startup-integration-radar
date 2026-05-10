"""Tests for the seed CSV manager: add, import, list, remove, update."""

import csv
from pathlib import Path

import pytest
from typer.testing import CliRunner

from app.services.seed_manager import (
    add_seed,
    import_domains,
    list_seeds,
    remove_seed,
    update_seed,
)
from scripts.radar import app


# ─── add_seed ────────────────────────────────────────────────────────────────

def test_add_seed_creates_file_and_normalizes_domain(tmp_path: Path):
    target = tmp_path / "seeds.csv"
    row, added = add_seed(
        domain="https://www.MONK.ai/about",
        company_name="Monk",
        category="automotive AI",
        notes="vehicle inspection",
        path=target,
    )
    assert added is True
    assert row.domain == "monk.ai"
    assert row.company_name == "Monk"

    # File contents match the canonical column order.
    with target.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert rows == [
        {
            "company_name": "Monk",
            "domain": "monk.ai",
            "category": "automotive AI",
            "notes": "vehicle inspection",
        }
    ]


def test_add_seed_dedupes_normalized_domain(tmp_path: Path):
    target = tmp_path / "seeds.csv"
    add_seed(domain="monk.ai", company_name="Monk", path=target)
    row, added = add_seed(
        domain="https://www.monk.ai/", company_name="Monk Renamed", path=target
    )
    assert added is False
    # Existing row is returned, not the would-be new row.
    assert row.company_name == "Monk"
    # File still has only one row.
    assert len(list_seeds(path=target)) == 1


def test_add_seed_rejects_unparseable_domain(tmp_path: Path):
    target = tmp_path / "seeds.csv"
    with pytest.raises(ValueError):
        add_seed(domain="   ", path=target)


# ─── import_domains ──────────────────────────────────────────────────────────

def test_import_domains_appends_and_dedupes(tmp_path: Path):
    target = tmp_path / "seeds.csv"
    add_seed(domain="monk.ai", path=target)

    added, skipped = import_domains(
        ["monk.ai", "https://openspace.ai", "  ", "# comment", "useparagon.com"],
        path=target,
    )

    added_domains = [row.domain for row in added]
    assert added_domains == ["openspace.ai", "useparagon.com"]
    assert skipped == ["monk.ai"]
    assert {row.domain for row in list_seeds(path=target)} == {
        "monk.ai",
        "openspace.ai",
        "useparagon.com",
    }


def test_import_domains_handles_blank_input(tmp_path: Path):
    target = tmp_path / "seeds.csv"
    added, skipped = import_domains([], path=target)
    assert added == []
    assert skipped == []
    # File should not be created if there's nothing to write.
    assert not target.exists()


# ─── list_seeds ──────────────────────────────────────────────────────────────

def test_list_seeds_returns_empty_when_file_missing(tmp_path: Path):
    target = tmp_path / "missing.csv"
    assert list_seeds(path=target) == []


def test_list_seeds_skips_rows_without_domain(tmp_path: Path):
    target = tmp_path / "seeds.csv"
    target.write_text(
        "company_name,domain,category,notes\n"
        "Monk,monk.ai,,\n"
        ",,,\n"               # blank
        "OpenSpace,,,\n",     # missing domain
        encoding="utf-8",
    )
    rows = list_seeds(path=target)
    assert [r.domain for r in rows] == ["monk.ai"]


# ─── remove_seed / update_seed ───────────────────────────────────────────────

def test_remove_seed_removes_existing_row(tmp_path: Path):
    target = tmp_path / "seeds.csv"
    add_seed(domain="monk.ai", path=target)
    add_seed(domain="openspace.ai", path=target)

    removed = remove_seed("https://www.monk.ai/about", path=target)
    assert removed is not None
    assert removed.domain == "monk.ai"
    assert {r.domain for r in list_seeds(path=target)} == {"openspace.ai"}


def test_remove_seed_returns_none_when_missing(tmp_path: Path):
    target = tmp_path / "seeds.csv"
    add_seed(domain="monk.ai", path=target)
    assert remove_seed("nope.example", path=target) is None


def test_update_seed_changes_only_passed_fields(tmp_path: Path):
    target = tmp_path / "seeds.csv"
    add_seed(domain="monk.ai", company_name="Monk", category="auto", notes="old", path=target)

    updated = update_seed("monk.ai", category="automotive AI", path=target)
    assert updated is not None
    assert updated.company_name == "Monk"  # unchanged
    assert updated.category == "automotive AI"  # changed
    assert updated.notes == "old"  # unchanged


# ─── Typer CLI smoke ─────────────────────────────────────────────────────────

runner = CliRunner()


def test_cli_add_domain_writes_file(tmp_path: Path):
    target = tmp_path / "seeds.csv"
    result = runner.invoke(
        app,
        [
            "add-domain",
            "monk.ai",
            "--name",
            "Monk",
            "--category",
            "automotive AI",
            "--path",
            str(target),
        ],
    )
    assert result.exit_code == 0
    assert "Added" in result.stdout
    assert {r.domain for r in list_seeds(path=target)} == {"monk.ai"}


def test_cli_add_domain_reports_duplicate(tmp_path: Path):
    target = tmp_path / "seeds.csv"
    add_seed(domain="monk.ai", path=target)
    result = runner.invoke(
        app, ["add-domain", "https://www.monk.ai/about", "--path", str(target)]
    )
    assert result.exit_code == 0
    assert "already exists" in result.stdout


def test_cli_import_domains_skips_duplicates(tmp_path: Path):
    target = tmp_path / "seeds.csv"
    add_seed(domain="monk.ai", path=target)
    domains_file = tmp_path / "domains.txt"
    domains_file.write_text("monk.ai\nopenspace.ai\n# skip me\nuseparagon.com\n")

    result = runner.invoke(
        app, ["import-domains", str(domains_file), "--path", str(target)]
    )
    assert result.exit_code == 0
    assert "Added 2" in result.stdout
    assert "skipped 1" in result.stdout


def test_cli_remove_domain_returns_zero_when_missing(tmp_path: Path):
    target = tmp_path / "seeds.csv"
    target.write_text("company_name,domain,category,notes\n")
    result = runner.invoke(
        app, ["remove-domain", "monk.ai", "--path", str(target)]
    )
    assert result.exit_code == 0
    assert "not found" in result.stdout
