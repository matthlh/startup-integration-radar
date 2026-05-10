from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from app.core.domain import normalize_domain


@dataclass
class SeedCompany:
    domain: str
    company_name: str = ""
    category: str = ""
    notes: str = ""


def parse_seed_csv(path: Path) -> list[SeedCompany]:
    """Parse a seed CSV into SeedCompany objects.

    Only 'domain' is required. company_name, category, and notes are optional.
    Supports legacy column names: 'name' for company_name, 'reason' for notes.
    Empty rows and rows with no valid domain are skipped silently.
    """
    companies: list[SeedCompany] = []

    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            raw_domain = (
                row.get("domain") or row.get("Domain") or ""
            ).strip()
            if not raw_domain:
                continue

            domain = normalize_domain(raw_domain)
            if not domain:
                continue

            companies.append(
                SeedCompany(
                    domain=domain,
                    company_name=(
                        row.get("company_name")
                        or row.get("name")
                        or row.get("Company Name")
                        or ""
                    ).strip(),
                    category=(row.get("category") or row.get("Category") or "").strip(),
                    notes=(row.get("notes") or row.get("reason") or row.get("Notes") or "").strip(),
                )
            )

    return companies
