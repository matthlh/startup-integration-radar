from __future__ import annotations

import asyncio
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import csv

import typer
from rich.console import Console
from rich.table import Table

from app.providers.exa import ExternalCallsDisabled
from app.services.csv_importer import parse_seed_csv
from app.services.discovery import discover_candidates
from app.services.exporter import companies_to_csv, filter_companies
from app.services.profiler import profile_company
from app.storage.json_store import CompanyStore

app = typer.Typer(help="Integration Scout CLI")
console = Console()
store = CompanyStore()


DEFAULT_DISCOVERY_CSV = Path("data/discovered_seeds.csv")


def _write_seed_csv(candidates, path: Path) -> None:
    """Write DiscoveryCandidate list to a CSV compatible with parse_seed_csv."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["company_name", "domain", "category", "notes"])
        writer.writeheader()
        for candidate in candidates:
            writer.writerow({
                "company_name": candidate.name,
                "domain": candidate.domain,
                "category": "",
                "notes": (candidate.reason or "").replace("\n", " ").strip()[:300],
            })


@app.command()
def discover(
    query: str,
    limit: int = typer.Option(20, "--limit"),
    live: bool = typer.Option(
        False,
        "--live",
        help="Call the Exa API. Requires ENABLE_EXTERNAL_API_CALLS=true and EXA_API_KEY in .env.",
    ),
    save: Path = typer.Option(
        DEFAULT_DISCOVERY_CSV,
        "--save",
        help="Where to write the seed CSV. Pass --save '' to skip writing.",
    ),
):
    """Discover candidate companies and save them to a seed CSV for review.

    Discovery does NOT auto-analyze companies. Review the generated CSV first,
    edit/remove rows, then run `analyze-csv` against the same path.

    Dry-run uses a built-in fallback list. Pass --live to call Exa (requires
    ENABLE_EXTERNAL_API_CALLS=true and EXA_API_KEY in your .env).
    """

    async def _run():
        try:
            return await discover_candidates(query, limit=limit, dry_run=not live)
        except ExternalCallsDisabled as exc:
            console.print(f"[red]External API calls are disabled:[/red] {exc}")
            console.print(
                "Set [bold]ENABLE_EXTERNAL_API_CALLS=true[/bold] and [bold]EXA_API_KEY=...[/bold] "
                "in [cyan].env[/cyan] to enable live discovery. Re-running in dry-run mode now."
            )
            return await discover_candidates(query, limit=limit, dry_run=True)

    candidates = asyncio.run(_run())

    table = Table(title=f"Discovery candidates ({'live: Exa' if live else 'dry-run'})")
    table.add_column("Name")
    table.add_column("Domain")
    table.add_column("Reason")
    for candidate in candidates:
        table.add_row(candidate.name, candidate.domain, candidate.reason[:80])
    console.print(table)

    if str(save):
        _write_seed_csv(candidates, save)
        console.print(
            f"\n[green]Saved {len(candidates)} candidates to[/green] [cyan]{save}[/cyan]"
        )
        console.print(
            f"Review the CSV, then run: [bold]python scripts/radar.py analyze-csv {save}[/bold]"
        )
    else:
        console.print("\n[yellow]Skipped writing seed CSV (--save '').[/yellow]")


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


@app.command("analyze-csv")
def analyze_csv(
    path: Path = typer.Argument(Path("data/seed_companies.csv")),
    use_llm: bool = False,
):
    """Analyze companies from a CSV file.

    Columns: domain (required), company_name, category, notes (all optional).
    Results are saved to the local store and can be exported with 'export'.
    """
    if not path.exists():
        console.print(f"[red]File not found:[/red] {path}")
        raise typer.Exit(1)

    seeds = parse_seed_csv(path)
    if not seeds:
        console.print(f"[yellow]No valid domains found in {path}[/yellow]")
        raise typer.Exit(0)

    console.print(f"Found [bold]{len(seeds)}[/bold] companies in {path.name} — analyzing...")

    async def _run() -> tuple[list[str], list[tuple[str, str]]]:
        successes: list[str] = []
        failures: list[tuple[str, str]] = []

        table = Table(title=f"Results from {path.name}")
        table.add_column("Company")
        table.add_column("Domain")
        table.add_column("Score", justify="right")
        table.add_column("Confidence")
        table.add_column("Stage")

        for seed in seeds:
            try:
                profile = await profile_company(seed.domain, use_llm=use_llm)
                if seed.company_name:
                    profile.name = seed.company_name
                if seed.category:
                    profile.category = seed.category
                store.upsert(profile)
                table.add_row(
                    profile.name,
                    profile.domain,
                    str(profile.score),
                    profile.confidence.value,
                    profile.stage.value,
                )
                successes.append(profile.domain)
            except Exception as exc:
                failures.append((seed.domain, str(exc)))
                table.add_row(seed.domain, seed.domain, "—", "—", "[red]error[/red]")

        console.print(table)
        return successes, failures

    successes, failures = asyncio.run(_run())

    console.print(
        f"\n[green]✓ {len(successes)} succeeded[/green]"
        + (f"  [red]✗ {len(failures)} failed[/red]" if failures else "")
    )
    for domain, error in failures:
        console.print(f"  [red]✗[/red] {domain}: {error[:100]}")


@app.command()
def export(
    path: Path = typer.Argument(Path("exports/clay_export.csv")),
    status: str = typer.Option(
        None,
        "--status",
        help="Filter by review_status (e.g. 'approved'). Default: export all companies.",
    ),
):
    """Export saved companies to a Clay-ready CSV.

    By default, all companies in the local store are exported. Pass --status approved
    (or any other review_status value) to export only matching companies.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    profiles = filter_companies(store.list(), status=status)
    csv_text = companies_to_csv(profiles)
    path.write_text(csv_text, encoding="utf-8")
    label = f" ({status} only)" if status else ""
    console.print(f"Wrote {path} — {len(profiles)} companies{label}")


@app.command()
def reset():
    """Clear the local JSON store."""
    store.clear()
    console.print("Cleared local store.")


if __name__ == "__main__":
    app()
