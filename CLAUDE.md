# CLAUDE.md — Integration Scout

Token-saving rules: keep this file under ~5k tokens. Detailed history lives in `docs/progress.md`. The active session's state lives in `session_summary.md` — read that first.

## Project summary

Integration Scout helps find B2B software companies that likely need customer-facing integrations built. It crawls public pages, scores integration-need signals, generates a Clay-ready CSV with per-company hypothesis, persona, suggested email, and demo concept. Runs locally; no auth, no email send, no paid APIs by default.

## What the app currently does

1. **Add seed companies** — CLI (`add-domain`, `import-domains`, `add`) or dashboard form, or edit `backend/data/seed_companies.csv` directly. Domains are normalized + deduped.
2. **Analyze** — fetches homepage + key pages (`/product`, `/integrations`, `/docs`, `/careers`, …), extracts signal evidence via keyword buckets in `signals.yaml`, infers category (page-type weighted, homepage dominates), picks destination systems (evidence-first, brand keywords beat category default).
3. **Score** — saturating buckets capped at 100; careers-page hits weigh 0.5×.
4. **Classify** — `fit_quality ∈ {strong_fit, possible_fit, weak_fit, bad_fit, mature_platform}` and `prospect_reasoning` (one sentence GTM angle). Bad-domain detection caps score at 20.
5. **Generate** — outreach subject/body and demo concept (deterministic; optional Claude path).
6. **Review** — Next.js dashboard with viewport-edge sidebar, search, quick filters, approve/reject/needs-research per card.
7. **Export** — Clay-ready CSV (27 stable columns) at `/api/exports/clay.csv?status=approved` or via CLI.

## Tech stack

- Backend: Python 3.9+, FastAPI, Pydantic v2, httpx, BeautifulSoup, Typer, Rich.
- Frontend: Next.js 15, React 19, TypeScript, Tailwind.
- Storage: local JSON file (`companies.json`) + CSV (`seed_companies.csv`). No DB.
- Tests: pytest (backend), `next build` (type-checks frontend).

## Key folders

```
backend/app/core/        scoring + signal extraction + signal_rules loader
backend/app/providers/   web fetcher, Exa, Anthropic (all gated)
backend/app/services/    profiler, persona, outreach, exporter, seed_manager,
                         destinations, fit_quality, competitive, csv_importer
backend/app/api/         FastAPI routes (/companies, /exports, /seeds, /health)
backend/app/storage/     CompanyStore JSON wrapper
backend/scripts/radar.py CLI (Typer)
backend/config/          signals.yaml — all scoring/persona/destination/competitor rules
backend/tests/           pytest suite (≥120 passing)
backend/data/            seed_companies.csv, companies.json (gitignored)
frontend/app/            Next.js routes (single page)
frontend/components/     CompanyCard, CompanySidebar
frontend/lib/            api client, shared types
docs/                    DEPLOYMENT.md, EDITING_SCORING_RULES.md, progress.md, …
```

## Local run commands

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
cp .env.example .env.local
npm run dev
# http://localhost:3000
```

## Important CLI commands

```bash
python scripts/radar.py add-domain monk.ai --name Monk   # add one seed
python scripts/radar.py add                              # interactive add
python scripts/radar.py import-domains domains.txt       # bulk add
python scripts/radar.py list-seeds | remove-domain | update-domain
python scripts/radar.py run                              # analyze + export, friendly summary
python scripts/radar.py analyze-csv data/seed_companies.csv
python scripts/radar.py export ../exports/clay.csv [--status approved]
python scripts/radar.py discover "<query>" --limit 25 [--live]
python scripts/radar.py reset                            # clear analyzed store
```

## Current UX problems

- Sidebar active-row tracks clicks only, not scroll position.
- No keyboard nav between sidebar rows.
- Sidebar filter is independent from the main grid filter (intentional but may confuse).
- No persistence of sidebar/filter state across reloads.
- No bulk-approve in dashboard.

## Current analysis-quality problems

- Mature-vertical SaaS (Samsara, Motive, ServiceTitan) doesn't auto-downgrade to `mature_platform` — the hint list only covers horizontal SaaS. Operator has to judge manually.
- Some sites block the crawler entirely (Artisan) — we correctly flag `bad_fit` but offer no fallback (e.g., trying a known sub-path).
- "Snowflake" can lead the destination list when found on a logistics page even when the more useful target would be TMS — evidence-first picker doesn't yet weight branded findings by relevance to category.
- Employee-count heuristic is still text-pattern-based; can fire on edge cases. Watch for unicorns mis-tagged founder.

## Current top priorities

See `session_summary.md` for the live "next" item. The standing roadmap (in rough order):

1. Add fallback sub-path crawling when homepage looks junky (snapsheet.com → snapsheetclaims.com style).
2. Weight evidence-first branded findings by category relevance so logistics doesn't lead with Snowflake.
3. Bulk-approve + scroll-tracked sidebar active state.
4. Move CLAUDE export columns into a documented schema file so changes are visible.

## Testing commands

```bash
cd backend && source .venv/bin/activate && pytest -q   # full backend suite (~120 tests)
cd frontend && npm run build                           # type-check + build
```

Run both when changes touch schema, scoring, or types. For pure docs/seed-CSV edits, neither is required.

## Hard constraints

- **Local-first.** No deployment is live. `docs/DEPLOYMENT.md` describes the Vercel + Railway/Render plan but nothing is deployed.
- **No auth.** Backend is wide open in dev.
- **No paid APIs by default.** `ENABLE_EXTERNAL_API_CALLS` gates Exa and Anthropic; both must fail safely when off or unkeyed.
- **No email sending.** Outreach copy is generated for review/Clay only.
- **Preserve existing CLI commands.** Renames are fine if the old name is kept as an alias for the current session.
- **Prefer small focused changes.** Multi-phase work is OK if each phase commits cleanly.
- **Run `pytest` and `npm run build`** when touching backend logic, schemas, or frontend types. Skip when changes are purely docs/data.
- **Don't commit `backend/data/companies.json` or `exports/*`.** They're gitignored. Edit `seed_companies.csv` is committed.
- **Scoring rules live in `signals.yaml`.** Never hardcode keywords/weights/categories/personas in Python.
