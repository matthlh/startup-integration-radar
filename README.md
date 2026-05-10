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

# Export saved companies to Clay CSV
python scripts/radar.py export ../exports/clay_export.csv

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

## What the CSV gives you

Each row in the Clay export includes:

- company name, domain, category
- score and confidence
- evidence summary (what signals were found and where)
- integration need hypothesis
- competitive trigger, if any
- primary persona and suggested contact titles
- outreach subject and body
- demo concept title
- blank columns for Clay-enriched contacts

## Recommended workflow

1. Edit `backend/data/seed_companies.csv` — add your target domains.
2. Run `python scripts/radar.py analyze-csv data/seed_companies.csv`.
3. Review cards in the dashboard — check score, evidence, persona.
4. Run `python scripts/radar.py export ../exports/clay_export.csv`.
5. Upload CSV to Clay and enrich contacts.
6. Send 10 personalized emails manually.
7. Build Vercel demos for high-score non-responders.
8. Only then automate more discovery with Exa.

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
