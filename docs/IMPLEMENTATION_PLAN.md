# Implementation Plan

## Phase 0: Repo sanity

- Run backend tests.
- Run backend CLI with fallback discovery.
- Start FastAPI.
- Start frontend.

Acceptance:

```bash
cd backend && pytest
python scripts/radar.py discover "companies like Monk"
python scripts/radar.py analyze monk.ai
```

## Phase 1: Manual prospecting MVP

Goal: generate the first 25 reviewed companies without live paid tools.

Tasks:

1. Add/import seed domains in `backend/data/seed_companies.csv`.
2. Run batch analysis.
3. Review score/evidence in dashboard.
4. Manually fix categories and false positives.
5. Export to Clay CSV.

Acceptance:

- `exports/clay_export.csv` has 25 rows.
- Each row has score, evidence summary, suggested titles, outreach body, and demo concept.

## Phase 2: Better scoring

Goal: reduce obvious false positives.

Tasks:

1. Expand negative signal rules.
2. Add industry-specific customer systems.
3. Add tests for automotive, construction, sales automation, and consumer disqualifier cases.
4. Improve confidence calculation.

Acceptance:

- High-fit examples score 75+.
- Consumer/local/agency-only examples score below 45 or disqualify.

## Phase 3: Clay enrichment handoff

Goal: make the CSV directly useful inside Clay.

Tasks:

1. Confirm column names match Clay workflow.
2. Add `contact_search_query` field.
3. Add `recommended_linkedin_titles` field.
4. Add `personalization_prompt` field.
5. Document Clay steps.

Acceptance:

- Import CSV into Clay.
- Enrich company LinkedIn, headcount, funding, and 1-2 contacts.
- Export final outreach list.

## Phase 4: Exa discovery

Goal: turn seed companies into 100 candidates.

Tasks:

1. Update `providers/exa.py` to match chosen Exa endpoint/SDK.
2. Add search templates from `prompts/exa_discovery_queries.md`.
3. Deduplicate domains.
4. Batch analyze results.

Acceptance:

- One command produces 100 candidate domains.
- At least 50 can be analyzed successfully.

## Phase 5: Figma Make UI polish

Goal: make the dashboard feel like a GTM command center.

Tasks:

1. Use `docs/FIGMA_MAKE_HANDOFF.md` to create a prototype.
2. Implement evidence drawer.
3. Add filters: score, stage, category, confidence.
4. Add review actions: approve, reject, needs research.

Acceptance:

- User can review 100 companies in under 30 minutes.

## Phase 6: Demo concept generator

Goal: make top prospects demo-ready.

Tasks:

1. Add a `demo brief` export for top 10.
2. Create Vercel demo prompt from company data.
3. Include public assets needed and integration flow.

Acceptance:

- Top 10 companies each have a Vercel-ready demo brief.

## Implemented checklist layer

The project now includes the first real GTM upgrades:

1. `evidence_summary` on every company profile.
2. Persona selection by estimated company size.
3. Deterministic demo concept generation with optional Claude JSON generation.
4. Competitive trigger detection for Merge.dev and Paragon.
5. Clay export columns for competitive trigger and angle.

Next implementation work should focus on CSV seed import, manual review status changes, and live Exa discovery.
