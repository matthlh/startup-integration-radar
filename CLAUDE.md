# CLAUDE.md

You are working on **Rutter Integration Radar**, an evidence-first GTM tool for finding companies with likely integration pain.

## Read first

Before coding, read these files:

1. `README.md`
2. `PRD.md`
3. `docs/IMPLEMENTATION_PLAN.md`
4. `docs/SCORING_RUBRIC.md`
5. `docs/OUTBOUND_PLAYBOOK.md`
6. `docs/FIGMA_MAKE_HANDOFF.md` if touching frontend

## Product mental model

This is not a generic scraper. The product should help answer:

> “Is this company likely to need customer-facing integrations badly enough that Rutter or an integration services team should outbound them?”

Every company should become a reviewable GTM card:

- What the company does
- Why integrations are likely painful
- Public evidence supporting that claim
- Whether a competitor trigger exists
- Who to contact
- What to say
- What demo to build if they do not respond

## Current acceptance criteria

Do not regress these features:

1. **Evidence Collector**
   - `CompanyProfile.evidence_summary` must exist.
   - It should mention matched keywords and source context when possible.
   - Example: `Mentioned 'NetSuite' and 'QuickBooks' on their engineering job posting.`

2. **Persona Logic**
   - If `employee_count_estimate < 50`, primary persona is Founder.
   - If `employee_count_estimate > 50`, primary persona is Product, with Partnerships as secondary.
   - Unknown size should still return a useful default and not crash.

3. **Demo Concept Generator**
   - Deterministic fallback must work without paid API calls.
   - Optional Claude path must return strict JSON and gracefully fall back if unavailable.

4. **Competitive Trigger**
   - Detect Merge.dev and Paragon signals from page text, links, image alt text, and asset names.
   - If triggered, outreach/demo should use a Rutter comparison angle instead of a generic integration angle.

## Architecture

```text
backend/app/core/        deterministic domain, signal, evidence, and scoring logic
backend/app/providers/   external APIs and website fetching
backend/app/services/    product workflows: profile, persona, outreach, discovery, export, competitive triggers
backend/app/storage/     local JSON store for MVP
backend/app/api/         FastAPI routes
backend/scripts/         CLI commands
frontend/                Next.js review dashboard
prompts/                 LLM and GTM prompts
```

## Development rules

1. Keep the deterministic pipeline useful without LLM calls.
2. Do not make paid API calls by default.
3. Put all provider-specific code behind `backend/app/providers/`.
4. Preserve evidence traceability. A score without evidence is not useful.
5. Add or update tests for scoring/rubric/persona changes.
6. Prefer small, reviewable changes.
7. Do not add auth, email sending, queues, or background jobs until the MVP is validated.
8. Do not commit secrets or generated data exports.

## External API rules

- `ENABLE_EXTERNAL_API_CALLS=false` means no live Exa or Claude calls.
- If implementing provider changes, keep dry-run behavior working.
- Exa discovery should return `DiscoveryCandidate` objects only.
- Claude analysis/demo generation should return structured JSON only.

## Testing

Run from `backend/`:

```bash
pytest
```

If touching frontend:

```bash
npm run build
```

## First recommended Claude Code task

```text
Read CLAUDE.md, PRD.md, and docs/IMPLEMENTATION_PLAN.md. Inspect the repo. Do not code yet. Summarize the architecture, then recommend the smallest next task.
```

## High-priority improvements

1. CSV import of seed domains.
2. Better company one-liner extraction from meta descriptions.
3. Manual review status updates.
4. Clay import merge after enrichment.
5. Exa live discovery provider update.
6. Figma Make UI polish.
7. Demo generator prompt for top 10 prospects.
8. Optional hosted deployment once the local workflow produces useful leads.
