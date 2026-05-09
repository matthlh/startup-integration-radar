# Rutter Integration Radar

Evidence-first GTM pipeline for finding companies that likely need customer-facing integrations.

This repo is intentionally **not** just a website scraper. It is a small GTM machine:

```text
Seed company or search query
→ discover candidate companies
→ crawl public pages and page assets/logos
→ extract integration evidence
→ detect competitive triggers
→ score integration need
→ choose target persona
→ generate outbound and demo concept
→ export to Clay for contact enrichment
```

The first seed was Monk-style companies: vertical AI/workflow businesses where customers probably need data synced into existing systems.

## Start here

Use this repo **locally first**. The MVP should prove it can produce useful leads before you host it for anyone else.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
pytest
```

Then run the dashboard:

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
http://localhost:3000
http://localhost:8000/docs
```

## Checklist upgrades implemented

### 1. Evidence Collector

Every `CompanyProfile` now returns an `evidence_summary` field directly from the API, not only in the CSV export.

Example output:

```text
Mentioned 'NetSuite' and 'QuickBooks' on their engineering job posting; mentioned 'webhooks' in developer documentation.
```

Evidence objects also track:

- `matched_keyword`
- `source_context`
- `source_url`
- `page_title`
- `signal`

### 2. Persona Logic

Implemented in `backend/app/services/persona.py`:

```text
< 50 people → Founder / CEO / Co-founder
> 50 people → Head of Product / VP Product, with Partnerships as secondary
unknown → Product first, Founder as validation fallback
```

The API returns both:

- `primary_persona`
- `personas[]`

### 3. Demo Concept Generator

Implemented in `backend/app/services/outreach.py`.

Default behavior is deterministic and free. If `use_llm=true` and `ENABLE_EXTERNAL_API_CALLS=true`, Claude generates a sharper JSON demo concept.

Example:

```text
Show them Rutter syncing automotive inspection data directly into an insurance claims dashboard.
```

### 4. Competitive Trigger

The crawler now inspects page text, links, and image/logo asset labels for competitors such as:

- Merge.dev
- Paragon / useparagon

If found, the product creates a `competitive_triggers[]` entry and changes the angle from:

```text
Why you need integrations
```

to:

```text
Why Rutter may be a better integration path than the current/visible competitor
```

This affects:

- `integration_need_hypothesis`
- outreach body
- demo concept
- Clay export columns

## CLI usage

```bash
cd backend
python scripts/radar.py discover "companies like Monk AI that need integrations" --limit 10
python scripts/radar.py analyze monk.ai merge.dev useparagon.com
python scripts/radar.py export ../exports/clay_export.csv
```

Live Exa/Claude calls are off by default. To enable later:

```env
ENABLE_EXTERNAL_API_CALLS=true
EXA_API_KEY=...
ANTHROPIC_API_KEY=...
```

## What to give your brother

The useful deliverable is the CSV plus demo candidates:

- 100 companies
- evidence-backed integration need hypothesis
- score and confidence
- competitive trigger, if any
- suggested contact titles
- suggested outbound subject/body
- demo concept for top companies
- blank columns for Clay-enriched contacts

## Recommended build sequence

1. Run manually on 20 seed domains.
2. Review false positives and improve `backend/app/core/signal_rules.py`.
3. Export CSV and enrich contacts in Clay.
4. Send 10 personalized emails manually.
5. Build 2 Vercel demos for high-score non-responders.
6. Only then automate more discovery with Exa.

## Hosted later, not first

Once the local CSV workflow produces useful leads, host it for your brother with:

- Vercel for frontend
- Render/Fly.io/Railway for FastAPI backend
- Supabase/Postgres instead of local JSON storage
- Basic password protection

Do not add hosting complexity until the prospecting motion works.
