# Project Start Plan

This project should start as a local GTM workbench, not a hosted SaaS.

## Decision

Run locally first.

Why:

- You can prove the workflow with 20 to 100 companies before adding hosting overhead.
- Clay should handle contact enrichment, email finding, and LinkedIn-like data work.
- The repo should handle the reasoning layer: evidence, scoring, persona, outbound angle, demo concept.

## Week 1 goal

Produce a useful Clay-ready CSV with 100 companies.

Each row should include:

- company name
- domain
- score
- evidence summary
- integration need hypothesis
- competitive trigger, if any
- primary persona
- suggested titles
- outreach subject
- outreach body
- demo concept

## Operator workflow

```text
1. Add seed companies or search queries.
2. Run discovery in dry-run or live Exa mode.
3. Analyze domains locally.
4. Review evidence summaries manually.
5. Export CSV.
6. Upload to Clay.
7. Use Clay to enrich contacts/emails.
8. Send a small batch manually.
9. Build Vercel demos for the best non-responders.
```

## Local commands

```bash
cd backend
pytest
python scripts/radar.py analyze monk.ai merge.dev useparagon.com
python scripts/radar.py export ../exports/clay_export.csv
```

## When to host

Host only after at least one of these happens:

- your brother wants to review leads himself
- you have 100+ leads and want shared review
- you need persistent storage across devices
- you want a cleaner workflow than CSV exports

Suggested hosted stack:

- Frontend: Vercel
- Backend: Render/Fly.io/Railway
- DB: Supabase Postgres
- Auth: simple password or invite-only auth
