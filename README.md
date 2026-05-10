# Integration Scout

Evidence-first GTM pipeline for finding B2B software companies that likely need customer-facing integrations built out as part of their product.

```text
Seed company or search query
→ discover candidate companies
→ crawl public pages and page assets/logos
→ extract integration evidence
→ detect competitive triggers
→ score integration need
→ choose target persona
→ generate outbound email and demo concept
→ export to Clay for contact enrichment
```

The first seed was monk.ai-style companies: vertical AI and workflow businesses where customers probably need data synced into existing systems like ERPs, CRMs, fleet management platforms, or claims systems.

## Start here

Use this repo **locally first**. Prove the workflow with 20–100 companies before hosting it.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
pytest
```

Then run the API:

```bash
uvicorn app.main:app --reload
```

In another terminal:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open:

```text
http://localhost:3000       — review dashboard
http://localhost:8000/docs  — FastAPI explorer
```

## Configuration

All scoring rules are in one file — no Python needed to tune detection:

```
backend/config/signals.yaml
```

Edit it to:

- Add or remove keywords for any signal
- Change `max_points` or `weight` for any signal
- Add competitors to detect (creates a different outreach angle)
- Set `your_company_name` for outreach templates

## CLI usage

```bash
cd backend

# Analyze companies from a CSV (the main batch workflow)
python scripts/radar.py analyze-csv data/seed_companies.csv

# Analyze one or more domains directly
python scripts/radar.py analyze monk.ai openspace.ai

# Analyze domains from a plain text file (one per line)
python scripts/radar.py analyze-file my_domains.txt

# Discover candidates (dry-run uses built-in fallback list)
python scripts/radar.py discover "vertical AI companies needing integrations"

# Export saved companies to Clay CSV (all companies by default)
python scripts/radar.py export ../exports/clay_export.csv

# Export only companies you've marked as approved in the dashboard
python scripts/radar.py export ../exports/clay_export.csv --status approved

# Reset the local store
python scripts/radar.py reset
```

## CSV seed file

The seed file lives at `backend/data/seed_companies.csv`. Only `domain` is required:

```csv
company_name,domain,category,notes
Monk,monk.ai,automotive,AI inspection platform — customers need fleet and claims sync
OpenSpace,openspace.ai,construction tech,Site documentation — customers need Procore/Autodesk sync
```

Supported columns:

| Column | Required | Description |
|---|---|---|
| `domain` | Yes | Company domain (e.g. `monk.ai`) |
| `company_name` | No | Overrides the name inferred from the domain |
| `category` | No | Overrides the category inferred from the page |
| `notes` | No | Freeform context — not used in scoring |

Add as many rows as you want. Run `analyze-csv` to process them all.

Live Exa/Claude calls are off by default. To enable:

```env
ENABLE_EXTERNAL_API_CALLS=true
EXA_API_KEY=...
ANTHROPIC_API_KEY=...
```

## Clay workflow

The Clay export hands company-level intelligence and persona suggestions to Clay,
which handles contact enrichment (emails, LinkedIn). This CSV intentionally does
not include contact rows — Clay adds those during enrichment.

```text
seed CSV → analyze CSV → export Clay CSV → upload to Clay → enrich contacts
```

```bash
# 1. seed CSV — add target domains to backend/data/seed_companies.csv
# 2. analyze CSV
python scripts/radar.py analyze-csv data/seed_companies.csv
# 3. export Clay CSV
python scripts/radar.py export ../exports/clay_export.csv
# 4. upload exports/clay_export.csv to Clay
# 5. enrich contacts in Clay (emails, LinkedIn, decision-maker filtering)
```

### Columns in the Clay export

Stable, Clay-friendly column names. Order is fixed.

| Column | Description |
|---|---|
| `company_name` | Inferred from domain or seed CSV |
| `domain` | Normalized (no protocol, no `www.`) |
| `website_url` | Full URL with protocol |
| `category` | Vertical inferred from homepage text |
| `score` | 0–100 integer score |
| `scoring_rules_version` | From `signals.yaml` — pin scores to a rules version |
| `scoring_profile_name` | From `signals.yaml` — name of the active rule profile |
| `scoring_explanation` | One-sentence explanation including confidence and strong signals |
| `signal_score_breakdown` | Human-readable: `integration language: 15/15; developer surface: 12/15` |
| `evidence_summary` | What was matched and where (e.g. careers page, docs) |
| `integration_need_hypothesis` | Why this company likely needs integrations built |
| `primary_persona` | `product`, `partnerships`, `engineering`, `solutions`, `founder`, `revenue` |
| `secondary_personas` | Semicolon-separated personas, primary excluded |
| `suggested_contact_titles` | Full deduplicated title list across all recommended personas |
| `clay_contact_search_titles` | Top 4 titles, primary persona first — feed straight into Clay's search |
| `competitor_or_existing_stack_trigger` | Detected integration platform (Merge.dev, Paragon, …) and outreach angle, if any |
| `demo_concept` | Title \| hypothesis \| first two steps |
| `suggested_email_subject` | Outbound subject line |
| `suggested_email_body` | Outbound body — review and edit in Clay before sending |
| `source_pages_scanned` | Semicolon-separated URLs the analysis read |
| `review_status` | Defaults to `new` — flip to `approved` / `skip` in Clay |
| `notes` | Free-form scratch field for manual annotations |

### Review and approval

Each company in the local store carries a `review_status` field (`new` by default). Mark companies as approved before running an approved-only export:

```bash
# Mark a single company approved (also reachable from the dashboard)
curl -X PATCH http://localhost:8000/api/companies/monk.ai/review_status \
  -H "content-type: application/json" \
  -d '{"review_status": "approved"}'
```

Export endpoints:

| Endpoint | Behavior |
|---|---|
| `GET /api/exports/clay.csv` | Exports every company in the store |
| `GET /api/exports/clay.csv?status=approved` | Exports only companies with `review_status=approved` |
| `python scripts/radar.py export <path>` | CLI: exports all by default |
| `python scripts/radar.py export <path> --status approved` | CLI: exports only approved |

The dashboard exposes both via the **Export all** and **Export approved** buttons in the header.

### After enrichment

1. Review cards in the dashboard — check score, evidence, persona — and mark approved.
2. Run the approved-only export and upload to Clay.
3. Send 10 personalized emails manually before automating.
4. Build Vercel demos for high-score non-responders.
5. Only then automate more discovery with Exa.

## Architecture

```
backend/app/core/       scoring, signal extraction, evidence summarization
backend/app/providers/  web fetcher, Claude, Exa (all gated)
backend/app/services/   profiler, persona, outreach, competitive, exporter, discovery
backend/app/storage/    local JSON store
backend/app/api/        FastAPI routes
backend/config/         signals.yaml — all scoring rules
backend/scripts/        CLI
frontend/               Next.js dashboard
```

## Hosting later, not first

Once the local CSV workflow produces useful leads:

- Frontend: Vercel
- Backend: Render / Fly.io / Railway
- DB: Supabase Postgres
- Auth: simple password protection

Do not add hosting complexity until the prospecting motion works.
