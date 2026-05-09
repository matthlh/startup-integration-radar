from __future__ import annotations

import asyncio
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import typer
from rich.console import Console
from rich.table import Table

from app.services.discovery import discover_candidates
from app.services.exporter import companies_to_csv
from app.services.profiler import profile_company
from app.storage.json_store import CompanyStore

app = typer.Typer(help="Integration Scout CLI")
console = Console()
store = CompanyStore()


@app.command()
def discover(query: str, limit: int = 20, live: bool = False):
    """Discover candidate companies. Dry-run uses built-in fallback candidates."""

    async def _run():
        candidates = await discover_candidates(query, limit=limit, dry_run=not live)
        table = Table(title="Discovery candidates")
        table.add_column("Name")
        table.add_column("Domain")
        table.add_column("Reason")
        for candidate in candidates:
            table.add_row(candidate.name, candidate.domain, candidate.reason[:80])
        console.print(table)

    asyncio.run(_run())


@app.command()
def analyze(domains: list[str], use_llm: bool = False):
    """Analyze and save one or more domains."""

    async def _run():
        table = Table(title="Analyzed companies")
        table.add_column("Company")
        table.add_column("Domain")
        table.add_column("Score", justify="right")
        table.add_column("Confidence")
        table.add_column("Stage")
        for domain in domains:
            profile = await profile_company(domain, use_llm=use_llm)
            store.upsert(profile)
            table.add_row(profile.name, profile.domain, str(profile.score), profile.confidence.value, profile.stage.value)
        console.print(table)

    asyncio.run(_run())


@app.command("analyze-file")
def analyze_file(path: Path, use_llm: bool = False):
    """Analyze domains from a plain text file, one domain per line."""
    domains = [line.strip() for line in path.read_text().splitlines() if line.strip() and not line.startswith("#")]
    analyze(domains, use_llm=use_llm)


@app.command()
def export(path: Path = typer.Argument(Path("exports/clay_export.csv"))):
    """Export saved companies to a Clay-ready CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    csv_text = companies_to_csv(store.list())
    path.write_text(csv_text, encoding="utf-8")
    console.print(f"Wrote {path}")


@app.command()
def reset():
    """Clear the local JSON store."""
    store.clear()
    console.print("Cleared local store.")


if __name__ == "__main__":
    app()
