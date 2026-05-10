# Integration Scout

Integration Scout helps you find B2B software companies that probably need customer-facing integrations built — and turns that finding into a Clay-ready CSV with a suggested persona, email, and demo concept for each company.

You give it a list of domains. It crawls the public website, looks for evidence of integration work (APIs, "Salesforce / NetSuite" mentions, partner pages, competitor logos like Merge.dev or Paragon, etc.), scores how likely each company is to need integration help, and writes everything to one spreadsheet you can hand to Clay for contact enrichment.

It runs **locally** on your laptop. No accounts, no signup, no email sending.

---

## 5-minute quick start

You'll need Python 3.9+ and Node 18+.

```bash
# 1. Install
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# 2. Add a company
python scripts/radar.py add-domain monk.ai --name Monk

# 3. Analyze + export — one command
python scripts/radar.py run

# 4. Upload exports/clay_export.csv to Clay. Done.
```

That's it. The dashboard is optional but useful — see "Daily workflow" below.

---

## Daily workflow

```text
add domains  →  run  →  review in dashboard  →  export approved  →  upload to Clay
```

1. **Add domains** to the seed list (one of three ways — see "Adding companies").
2. **Run** the analysis: `python scripts/radar.py run`.
3. **Review in the dashboard** at <http://localhost:3000>. Each card shows the score, why the company likely needs integrations, the suggested persona and contact titles, the suggested email, and a demo concept. Click **Approve**, **Needs research**, or **Reject**.
4. **Export only approved companies**: `python scripts/radar.py export ../exports/clay_export.csv --status approved`.
5. **Upload to Clay** — Clay handles email/LinkedIn enrichment from there.

To start the dashboard:

```bash
# Terminal 1 — backend API
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2 — frontend
cd frontend
npm install        # first time only
cp .env.example .env.local
npm run dev

# Then open
open http://localhost:3000
```

---

## How to add companies

There are four ways. Pick whichever feels easiest.

### One company, quick (recommended)

```bash
python scripts/radar.py add-domain monk.ai --name Monk \
  --category "automotive AI" \
  --notes "vehicle inspection platform"
```

`--name`, `--category`, and `--notes` are all optional. The domain is normalized automatically: `https://www.monk.ai/about` → `monk.ai`.

### One company, interactive

```bash
python scripts/radar.py add
# then answer the prompts for domain, name, category, notes
```

### A list of domains in a text file

Create a file like `my_domains.txt` with one domain per line (lines starting with `#` are ignored):

```text
monk.ai
openspace.ai
useparagon.com
# tractable.ai is already in the list
```

Then:

```bash
python scripts/radar.py import-domains my_domains.txt
```

Duplicates already in the seed CSV are skipped automatically.

### Edit the CSV directly

`backend/data/seed_companies.csv` is a normal CSV — open it in Excel/Numbers/Google Sheets and add rows. Columns: `company_name, domain, category, notes`. Only `domain` is required.

### Useful related commands

```bash
python scripts/radar.py list-seeds                     # show every domain in the seed CSV
python scripts/radar.py remove-domain monk.ai          # delete a row
python scripts/radar.py update-domain monk.ai \
    --name "Monk AI" --category "automotive"           # change one or more fields
```

All of these dedupe and normalize domains for you.

---

## How to review leads

After running the analysis you have two ways to review.

### In the dashboard (best)

```bash
# Backend (one terminal)
uvicorn app.main:app --reload
# Frontend (another terminal)
cd frontend && npm run dev
```

Then open <http://localhost:3000>. Each card shows:

- score and confidence band (Hot / Warm / Watch)
- a short company summary pulled from the homepage
- why this company likely needs integrations
- evidence summary (the keywords and pages that triggered each signal)
- suggested persona (Founder / Product / Partnerships / Engineering / Solutions)
- suggested contact titles to feed into Clay
- suggested email subject and body (click "Show body" to expand)
- demo concept title and first three steps
- a crawl-quality warning when the homepage looked parked or returned junk

The **Approve / Needs research / Reject** buttons on each card update review status immediately. Use the filter dropdowns to narrow by review status or pipeline stage.

### From the CLI

```bash
python scripts/radar.py list-seeds       # what's queued up
python scripts/radar.py export ../exports/clay_export.csv   # full CSV — open in Excel
```

---

## How to export to Clay

```bash
# Everything in the local store
python scripts/radar.py export ../exports/clay_export.csv

# Only companies you marked "Approve" in the dashboard
python scripts/radar.py export ../exports/clay_export.csv --status approved
```

The CSV has 27 stable Clay-friendly columns including `company_name`, `domain`, `score`, `signal_score_breakdown` (human-readable), `evidence_summary`, `integration_need_hypothesis`, `primary_persona`, `clay_contact_search_titles`, `suggested_email_subject`, `suggested_email_body`, `review_status`, and `crawl_quality_warning`. Upload the file to Clay and use it for contact enrichment.

The same CSV is available at `GET http://localhost:8000/api/exports/clay.csv` (and `?status=approved`) when the backend is running.

---

## How to edit scoring rules

All scoring rules live in **`backend/config/signals.yaml`**. Edit that file in any text editor — no Python changes needed.

Common edits:

- **Add a keyword** to an existing signal (e.g. add `"workato"` to `competitor_presence` keywords).
- **Add a new competitor** to the `competitors:` block — its display name shows up in outreach as the angle.
- **Add a vertical** to the `categories:` block.
- **Change persona routing** — the `persona_rules:` block controls who shows up as primary/secondary based on company size and detected signals.

Full walk-through with examples: [docs/EDITING_SCORING_RULES.md](docs/EDITING_SCORING_RULES.md).

After editing, re-run analysis: `python scripts/radar.py run`.

---

## Troubleshooting

**`File not found: data/seed_companies.csv`** — you're running from the wrong directory. Run all CLI commands from inside `backend/` with the venv active.

**`No valid domains found`** — your CSV has a header row but no data rows, or the `domain` column is empty. Run `python scripts/radar.py list-seeds` to confirm.

**A company scores 0 / "low" with no evidence** — the homepage probably blocked the crawler or returned junk. Look for the **Crawl warning** chip in the dashboard. You can re-run with a different `User-Agent` (set `USER_AGENT=` in `.env`) or remove the row.

**The dashboard is empty after `npm run dev`** — make sure the backend is running on port 8000 and that `frontend/.env.local` contains `NEXT_PUBLIC_API_BASE=http://localhost:8000/api`.

**`External API calls are disabled`** — Exa discovery is gated by two settings. Add `ENABLE_EXTERNAL_API_CALLS=true` and `EXA_API_KEY=...` to `backend/.env` and pass `--live` to the discover command.

**Tractable / a unicorn shows up as `primary_persona=founder`** — the employee-count heuristic mis-fired on phrases like "founding team". Override by passing `--name` and a real category in `add-domain`, or just trust your own judgment in the dashboard.

**I want to start over** — `python scripts/radar.py reset` clears all analyzed results. The seed CSV is untouched. Re-run `python scripts/radar.py run` to rebuild.

**Tests** — from `backend/`: `pytest`. Frontend types: `cd frontend && npm run build`.

---

## All CLI commands

```bash
python scripts/radar.py --help          # show this list
python scripts/radar.py add             # add one company interactively
python scripts/radar.py add-domain      # add one company by domain + flags
python scripts/radar.py import-domains  # add a list of domains from a .txt file
python scripts/radar.py list-seeds      # show seed CSV contents
python scripts/radar.py remove-domain   # delete a seed row
python scripts/radar.py update-domain   # change name/category/notes on a seed row
python scripts/radar.py discover        # find candidate companies (dry-run or Exa)
python scripts/radar.py analyze         # analyze one or more domains directly
python scripts/radar.py analyze-file    # analyze domains from a .txt file
python scripts/radar.py analyze-csv     # analyze every domain in a CSV
python scripts/radar.py export          # write a Clay-ready CSV
python scripts/radar.py run             # analyze-csv + export + summary
python scripts/radar.py reset           # clear analyzed results
```

Every command has its own `--help` with examples.

---

## Architecture

```
backend/app/core/        scoring + signal extraction
backend/app/providers/   web fetcher, Exa, Anthropic
backend/app/services/    profiler, persona, outreach, exporter, seed manager
backend/app/storage/     local JSON store
backend/app/api/         FastAPI routes
backend/config/          signals.yaml — edit this to tune scoring
backend/scripts/radar.py CLI
frontend/                Next.js dashboard
```

External calls are **off** by default:

- **Exa** is used only for discovery and only when `ENABLE_EXTERNAL_API_CALLS=true` *and* `EXA_API_KEY` is set. If either is missing, the CLI prints a clear message and falls back to a built-in dry-run candidate list.
- **Anthropic** is optional and only powers the demo-concept LLM path. The deterministic fallback works fine without a key.

No email sending. No LinkedIn scraping. No paid contact enrichment — Clay handles that.
