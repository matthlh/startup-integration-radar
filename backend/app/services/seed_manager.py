"""CRUD helpers for the seed CSV (`backend/data/seed_companies.csv`).

The file lives in plain CSV so the user can also edit it in Excel/Google Sheets,
but every command goes through this module so we always:
  * normalize the domain (strip protocol, www., trailing slashes),
  * dedupe by normalized domain (case-insensitive),
  * preserve any extra columns the user added by hand.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from app.config import get_settings
from app.core.domain import normalize_domain


SEED_COLUMNS = ["company_name", "domain", "category", "notes"]


def _default_seed_path() -> Path:
    return get_settings().seed_csv_path


# Kept as a property-like accessor so tests can monkeypatch DATA_DIR before
# the module is imported.
DEFAULT_SEED_PATH = _default_seed_path()


@dataclass
class SeedRow:
    domain: str
    company_name: str = ""
    category: str = ""
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "company_name": self.company_name,
            "domain": self.domain,
            "category": self.category,
            "notes": self.notes,
        }


def _resolve(path: Path | None) -> Path:
    # Re-read the default each call so DATA_DIR overrides set at runtime
    # (e.g. in tests via monkeypatch) take effect.
    return path if path is not None else _default_seed_path()


def list_seeds(path: Path | None = None) -> list[SeedRow]:
    """Return all seed rows. Empty list if the file doesn't exist yet."""
    target = _resolve(path)
    if not target.exists():
        return []
    rows: list[SeedRow] = []
    with target.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            domain = (row.get("domain") or "").strip()
            if not domain:
                continue
            normalized = normalize_domain(domain)
            if not normalized:
                continue
            rows.append(
                SeedRow(
                    domain=normalized,
                    company_name=(row.get("company_name") or row.get("name") or "").strip(),
                    category=(row.get("category") or "").strip(),
                    notes=(row.get("notes") or row.get("reason") or "").strip(),
                )
            )
    return rows


def _write_seeds(rows: list[SeedRow], path: Path | None = None) -> None:
    target = _resolve(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=SEED_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.to_dict())


def add_seed(
    domain: str,
    company_name: str = "",
    category: str = "",
    notes: str = "",
    path: Path | None = None,
) -> tuple[SeedRow, bool]:
    """Append one row to the seed CSV.

    Returns (row, added). `added` is False if a row with the same normalized
    domain already exists; in that case the existing row is returned unchanged
    so the caller can print a friendly "already exists" message.
    """
    normalized = normalize_domain(domain)
    if not normalized:
        raise ValueError(f"Could not normalize domain: {domain!r}")

    existing = list_seeds(path)
    for row in existing:
        if row.domain == normalized:
            return row, False

    new_row = SeedRow(
        domain=normalized,
        company_name=company_name.strip(),
        category=category.strip(),
        notes=notes.strip(),
    )
    existing.append(new_row)
    _write_seeds(existing, path)
    return new_row, True


def import_domains(
    domains: list[str], path: Path | None = None
) -> tuple[list[SeedRow], list[str]]:
    """Append a flat list of domains to the seed CSV, skipping duplicates.

    Returns (added, skipped) where `skipped` contains the normalized domains
    that already existed in the file.
    """
    existing = list_seeds(path)
    by_domain = {row.domain: row for row in existing}
    added: list[SeedRow] = []
    skipped: list[str] = []

    for raw in domains:
        if not raw or raw.startswith("#"):
            continue
        try:
            normalized = normalize_domain(raw)
        except Exception:
            continue
        if not normalized:
            continue
        if normalized in by_domain:
            skipped.append(normalized)
            continue
        new_row = SeedRow(domain=normalized)
        existing.append(new_row)
        by_domain[normalized] = new_row
        added.append(new_row)

    if added:
        _write_seeds(existing, path)
    return added, skipped


def remove_seed(domain: str, path: Path | None = None) -> SeedRow | None:
    """Remove a seed row by domain. Returns the removed row, or None."""
    normalized = normalize_domain(domain)
    existing = list_seeds(path)
    keep = [row for row in existing if row.domain != normalized]
    if len(keep) == len(existing):
        return None
    removed = next(row for row in existing if row.domain == normalized)
    _write_seeds(keep, path)
    return removed


def update_seed(
    domain: str,
    company_name: str | None = None,
    category: str | None = None,
    notes: str | None = None,
    path: Path | None = None,
) -> SeedRow | None:
    """Update fields on an existing seed row. Returns the updated row, or None."""
    normalized = normalize_domain(domain)
    existing = list_seeds(path)
    for row in existing:
        if row.domain == normalized:
            if company_name is not None:
                row.company_name = company_name.strip()
            if category is not None:
                row.category = category.strip()
            if notes is not None:
                row.notes = notes.strip()
            _write_seeds(existing, path)
            return row
    return None
