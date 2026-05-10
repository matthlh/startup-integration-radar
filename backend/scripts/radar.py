"""Integration Scout — command line interface.

Most users only need three commands:

  add-domain monk.ai --name Monk     # add one company to the seed CSV
  run                                # analyze the seed CSV and write a Clay export
  open exports/clay_export.csv       # upload that file to Clay

See `python scripts/radar.py --help` for everything else, or the README for a
full walk-through.
"""

from __future__ import annotations

import asyncio
import csv
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import typer
from rich.console import Console
from rich.table import Table

from app.providers.exa import ExternalCallsDisabled
from app.services.csv_importer import parse_seed_csv
from app.services.discovery import discover_candidates
from app.services.exporter import companies_to_csv, filter_companies
from app.services.profiler import profile_company, refresh_derived_fields
from app.services.seed_manager import (
    DEFAULT_SEED_PATH,
    add_seed,
    import_domains,
    list_seeds,
    remove_seed,
    update_seed,
)
from app.storage.json_store import CompanyStore

app = typer.Typer(
    help=(
        "Integration Scout — find B2B companies that likely need integrations "
        "and ship a Clay-ready CSV.\n\n"
        "Quick start:\n"
        "  python scripts/radar.py add-domain monk.ai --name Monk\n"
        "  python scripts/radar.py run\n"
    ),
    no_args_is_help=True,
)
console = Console()
store = CompanyStore()


DEFAULT_DISCOVERY_CSV = Path("data/discovered_seeds.csv")
DEFAULT_SEED_CSV = Path("data/seed_companies.csv")
DEFAULT_EXPORT_CSV = Path("../exports/clay_export.csv")


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _write_seed_csv_from_candidates(candidates, path: Path) -> None:
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


# Kept under the old name so existing tests/imports don't break.
_write_seed_csv = _write_seed_csv_from_candidates


def _print_results_table(profiles, *, title: str) -> None:
    table = Table(title=title)
    table.add_column("Company")
    table.add_column("Domain")
    table.add_column("Score", justify="right")
    table.add_column("Confidence")
    table.add_column("Stage")
    for profile in profiles:
        table.add_row(
            profile.name,
            profile.domain,
            str(profile.score),
            profile.confidence.value,
            profile.stage.value,
        )
    console.print(table)


# ─── Seed CSV management ─────────────────────────────────────────────────────


@app.command("add-domain")
def add_domain(
    domain: str = typer.Argument(..., help="A domain like monk.ai or https://monk.ai/about."),
    name: str = typer.Option("", "--name", help="Company name (if you want to override the auto-derived one)."),
    category: str = typer.Option("", "--category", help="Optional vertical, e.g. 'automotive AI'."),
    notes: str = typer.Option("", "--notes", help="Free-form notes for the operator."),
    path: Path = typer.Option(DEFAULT_SEED_CSV, "--path", help="Seed CSV to append to."),
) -> None:
    """Add one domain to the seed CSV (data/seed_companies.csv).

    The domain is normalized: https://www.monk.ai/about → monk.ai. If the
    normalized domain already exists in the file, the row is left unchanged
    and the command prints a clear "already exists" message.

    Example:
      python scripts/radar.py add-domain monk.ai --name Monk \\
        --category "automotive AI" --notes "vehicle inspection platform"
    """
    try:
        row, added = add_seed(
            domain=domain,
            company_name=name,
            category=category,
            notes=notes,
            path=path,
        )
    except ValueError as exc:
        console.print(f"[red]Could not add domain:[/red] {exc}")
        raise typer.Exit(1)

    if added:
        console.print(
            f"[green]Added[/green] [bold]{row.domain}[/bold] to [cyan]{path}[/cyan]"
        )
    else:
        console.print(
            f"[yellow]{row.domain} already exists in {path}[/yellow] — no change."
        )


@app.command()
def add(path: Path = typer.Option(DEFAULT_SEED_CSV, "--path")) -> None:
    """Add one company interactively (prompts for each field).

    Reads/writes data/seed_companies.csv (or whatever --path points to).
    Same dedupe + normalization as add-domain.
    """
    domain = typer.prompt("Domain (required, e.g. monk.ai)").strip()
    if not domain:
        console.print("[red]Domain is required.[/red]")
        raise typer.Exit(1)

    name = typer.prompt("Company name (optional)", default="", show_default=False).strip()
    category = typer.prompt(
        "Category / vertical (optional, e.g. 'automotive AI')",
        default="",
        show_default=False,
    ).strip()
    notes = typer.prompt(
        "Notes for yourself (optional)", default="", show_default=False
    ).strip()

    add_domain(domain=domain, name=name, category=category, notes=notes, path=path)


@app.command("import-domains")
def import_domains_cmd(
    file: Path = typer.Argument(..., help="Plain text file with one domain per line. '#' lines are skipped."),
    path: Path = typer.Option(DEFAULT_SEED_CSV, "--path", help="Seed CSV to append to."),
) -> None:
    """Append a list of domains to the seed CSV without duplicates.

    The input is a plain text file like:

        monk.ai
        openspace.ai
        # this comment is ignored
        useparagon.com

    Domains are normalized and any that already exist in the seed CSV are
    skipped. The command reports how many were added vs. skipped.
    """
    if not file.exists():
        console.print(f"[red]File not found:[/red] {file}")
        raise typer.Exit(1)

    domains = [line.strip() for line in file.read_text().splitlines() if line.strip()]
    added, skipped = import_domains(domains, path=path)

    console.print(
        f"[green]Added {len(added)}[/green] new domain(s) to [cyan]{path}[/cyan]; "
        f"[yellow]skipped {len(skipped)}[/yellow] duplicate(s)."
    )
    for domain in added[:20]:
        console.print(f"  [green]+[/green] {domain.domain}")
    if skipped:
        for domain in skipped[:20]:
            console.print(f"  [yellow]·[/yellow] {domain} (already in {path})")


@app.command("list-seeds")
def list_seeds_cmd(
    path: Path = typer.Option(DEFAULT_SEED_CSV, "--path"),
) -> None:
    """Show every domain currently in the seed CSV.

    Reads data/seed_companies.csv (or --path).
    """
    rows = list_seeds(path=path)
    if not rows:
        console.print(
            f"[yellow]No seed companies in {path}.[/yellow] "
            f"Add some with: python scripts/radar.py add-domain <domain>"
        )
        return

    table = Table(title=f"Seed companies ({len(rows)} in {path.name})")
    table.add_column("Domain")
    table.add_column("Name")
    table.add_column("Category")
    table.add_column("Notes")
    for row in rows:
        table.add_row(row.domain, row.company_name, row.category, row.notes[:60])
    console.print(table)


@app.command("remove-domain")
def remove_domain_cmd(
    domain: str = typer.Argument(..., help="Domain to remove (any URL form is normalized)."),
    path: Path = typer.Option(DEFAULT_SEED_CSV, "--path"),
) -> None:
    """Remove a domain from the seed CSV.

    Does not affect already-analyzed results in the local store. To re-run
    after removing, just run `analyze-csv` again.
    """
    removed = remove_seed(domain, path=path)
    if removed is None:
        console.print(f"[yellow]{domain} not found in {path}[/yellow] — nothing to remove.")
        raise typer.Exit(0)
    console.print(f"[green]Removed[/green] [bold]{removed.domain}[/bold] from [cyan]{path}[/cyan].")


@app.command("update-domain")
def update_domain_cmd(
    domain: str = typer.Argument(..., help="Domain to update (any URL form is normalized)."),
    name: str = typer.Option(None, "--name", help="New company name."),
    category: str = typer.Option(None, "--category", help="New category."),
    notes: str = typer.Option(None, "--notes", help="New notes."),
    path: Path = typer.Option(DEFAULT_SEED_CSV, "--path"),
) -> None:
    """Update one or more fields on a seed row.

    Only the flags you pass are changed; everything else is left untouched.
    """
    if name is None and category is None and notes is None:
        console.print("[yellow]Pass at least one of --name, --category, --notes.[/yellow]")
        raise typer.Exit(1)
    updated = update_seed(domain, company_name=name, category=category, notes=notes, path=path)
    if updated is None:
        console.print(f"[yellow]{domain} not found in {path}[/yellow] — nothing to update.")
        raise typer.Exit(0)
    console.print(f"[green]Updated[/green] [bold]{updated.domain}[/bold].")


# ─── Discovery / analysis / export ───────────────────────────────────────────


@app.command()
def discover(
    query: str = typer.Argument(..., help="A natural-language search like 'AI inspection companies needing integrations'."),
    limit: int = typer.Option(20, "--limit", help="Max number of candidates to return."),
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
) -> None:
    """Find candidate companies and save them to a seed CSV for review.

    Discovery does NOT auto-analyze companies. Review the generated CSV first,
    edit/remove rows, then run `analyze-csv` against the same path.

    Dry-run uses a built-in fallback list. Pass --live to call Exa (requires
    ENABLE_EXTERNAL_API_CALLS=true and EXA_API_KEY in your .env).

    Writes to data/discovered_seeds.csv by default.
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
        _write_seed_csv_from_candidates(candidates, save)
        console.print(
            f"\n[green]Saved {len(candidates)} candidates to[/green] [cyan]{save}[/cyan]"
        )
        console.print(
            f"Review the CSV, then run: [bold]python scripts/radar.py analyze-csv {save}[/bold]"
        )
    else:
        console.print("\n[yellow]Skipped writing seed CSV (--save '').[/yellow]")


@app.command()
def analyze(
    domains: list[str] = typer.Argument(..., help="One or more domains to analyze."),
    use_llm: bool = typer.Option(False, "--use-llm"),
) -> None:
    """Analyze one or more domains and save the results to the local store.

    Useful for quickly testing the pipeline against a single domain. Most users
    should prefer `add-domain` + `run` instead.
    """

    async def _run():
        results = []
        for domain in domains:
            profile = await profile_company(domain, use_llm=use_llm)
            store.upsert(profile)
            results.append(profile)
        return results

    profiles = asyncio.run(_run())
    _print_results_table(profiles, title="Analyzed companies")


@app.command("analyze-file")
def analyze_file(
    path: Path = typer.Argument(..., help="Plain text file with one domain per line."),
    use_llm: bool = typer.Option(False, "--use-llm"),
) -> None:
    """Analyze domains from a plain text file (one domain per line).

    Lines starting with '#' are skipped. Same effect as `analyze a.com b.com c.com`.
    """
    domains = [line.strip() for line in path.read_text().splitlines() if line.strip() and not line.startswith("#")]
    analyze(domains, use_llm=use_llm)


@app.command("analyze-csv")
def analyze_csv(
    path: Path = typer.Argument(DEFAULT_SEED_CSV, help="Seed CSV to analyze."),
    use_llm: bool = typer.Option(False, "--use-llm"),
) -> None:
    """Analyze every company in a seed CSV and save the results.

    Reads: <path> (default data/seed_companies.csv).
    Writes: backend/data/companies.json (the local store).

    CSV columns: domain (required), company_name, category, notes (all optional).
    Re-running will overwrite the previous analysis for the same domain.
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
                category_overridden = bool(seed.category and seed.category != profile.category)
                if seed.category:
                    profile.category = seed.category
                if category_overridden:
                    # Re-derive hypothesis / outreach / demo so they reflect the
                    # seed-supplied category, not the inferred one.
                    await refresh_derived_fields(profile, use_llm=use_llm)
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
    path: Path = typer.Argument(DEFAULT_EXPORT_CSV, help="Output CSV path."),
    status: str = typer.Option(
        None,
        "--status",
        help="Filter by review_status (e.g. 'approved', 'skip', 'needs_research'). Default: export all companies.",
    ),
) -> None:
    """Write the local store to a Clay-ready CSV.

    Reads: backend/data/companies.json.
    Writes: <path> (default ../exports/clay_export.csv).

    By default every company is exported. Pass --status approved to export only
    companies you've marked approved in the dashboard.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    profiles = filter_companies(store.list(), status=status)
    csv_text = companies_to_csv(profiles)
    path.write_text(csv_text, encoding="utf-8")
    label = f" ({status} only)" if status else ""
    console.print(f"Wrote [cyan]{path}[/cyan] — {len(profiles)} companies{label}")


@app.command()
def run(
    seed: Path = typer.Option(DEFAULT_SEED_CSV, "--seed", help="Seed CSV to analyze."),
    out: Path = typer.Option(DEFAULT_EXPORT_CSV, "--out", help="Where to write the Clay export."),
    use_llm: bool = typer.Option(False, "--use-llm"),
) -> None:
    """One-command workflow: analyze the seed CSV, then export.

    Equivalent to:
      python scripts/radar.py analyze-csv <seed>
      python scripts/radar.py export <out>

    Prints a summary at the end including high-score counts and where to look next.
    """
    if not seed.exists():
        console.print(
            f"[red]Seed CSV not found:[/red] {seed}\n"
            f"Add at least one company first with: python scripts/radar.py add-domain <domain>"
        )
        raise typer.Exit(1)

    analyze_csv(path=seed, use_llm=use_llm)
    export(path=out, status=None)

    profiles = store.list()
    above_70 = sum(1 for p in profiles if p.score >= 70)
    above_80 = sum(1 for p in profiles if p.score >= 80)
    high_confidence = sum(1 for p in profiles if p.confidence.value == "high")

    console.print()
    console.print("[bold]Summary[/bold]")
    console.print(f"  Total companies analyzed: [bold]{len(profiles)}[/bold]")
    console.print(f"  Score ≥ 80: [bold green]{above_80}[/bold green]")
    console.print(f"  Score ≥ 70: [bold]{above_70}[/bold]")
    console.print(f"  High confidence: [bold]{high_confidence}[/bold]")
    console.print(f"  Export written to: [cyan]{out}[/cyan]")
    console.print()
    console.print("[bold]Next:[/bold]")
    console.print(f"  • Open the dashboard at [cyan]http://localhost:3000[/cyan] to review and approve leads.")
    console.print(f"  • Or upload [cyan]{out}[/cyan] to Clay directly.")
    console.print(
        f"  • Approved-only export: [bold]python scripts/radar.py export {out} --status approved[/bold]"
    )


@app.command()
def reset() -> None:
    """Clear the local JSON store of analyzed companies.

    Does NOT touch the seed CSV. Use this when you want to re-analyze everything
    from scratch.
    """
    store.clear()
    console.print("[green]Cleared local store.[/green] Seed CSV is unchanged.")


if __name__ == "__main__":
    app()
