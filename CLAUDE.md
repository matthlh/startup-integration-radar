# CLAUDE.md

You are working on **Integration Scout**, an evidence-first tool for finding B2B software companies that likely need customer-facing integrations, workflow connectors, data syncs, or API implementation work built out as part of their product offering.

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

> "Is this company likely to need customer-facing integrations badly enough that an integration services team should reach out to them?"

A company like monk.ai is a good example: they sell automotive inspection AI and their customers almost certainly need that data synced into fleet management systems, dealer management systems, or insurance claims platforms. They need integrations built.

Every company should become a reviewable GTM card:

- What the company does
- Why integrations are likely part of their product gap
- Public evidence supporting that claim
- Whether a competitor integration platform is already in play
- Who to contact
- What to say
- What demo concept to build if they do not respond

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
   - Detect integration platform signals (Merge.dev, Paragon, etc.) from page text, links, image alt text, and asset names.
   - If triggered, outreach/demo should use a comparison angle rather than a generic integration angle.

## Architecture

```text
backend/app/core/        deterministic domain, signal, evidence, and scoring logic
backend/app/providers/   external APIs and website fetching
backend/app/services/    product workflows: profile, persona, outreach, discovery, export, competitive triggers
backend/app/storage/     local JSON store for MVP
backend/app/api/         FastAPI routes
backend/scripts/         CLI commands
backend/config/          editable scoring rules (signals.yaml)
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
9. Scoring rules live in `backend/config/signals.yaml` — do not hardcode keywords or weights in Python.

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

## High-priority improvements

1. CSV import of seed domains.
2. Meta description extraction for better one-liners.
3. Manual review status updates in the dashboard.
4. Persona rules moved into signals.yaml.
5. Exa live discovery provider validation.
6. Outreach email body visible in the dashboard card.
7. Demo generator prompt for top 10 prospects.
