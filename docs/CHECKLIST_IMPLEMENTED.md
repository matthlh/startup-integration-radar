# Checklist Implemented

## Evidence Collector

Files:

- `backend/app/core/signals.py`
- `backend/app/schemas.py`
- `backend/app/services/exporter.py`

The API now returns `CompanyProfile.evidence_summary`.

Evidence captures:

- keyword found
- source context
- URL
- page title
- snippet
- signal type

Example summary:

```text
Mentioned 'NetSuite' and 'QuickBooks' on their engineering job posting.
```

## Persona Logic

Files:

- `backend/app/services/persona.py`
- `backend/app/services/profiler.py`

Rules:

```text
< 50 people → Founder
> 50 people → Head of Product / Partnerships
unknown → Product first, Founder validation fallback
```

The API returns:

- `employee_count_estimate`
- `primary_persona`
- `personas[]`

## Demo Concept Generator

Files:

- `backend/app/services/outreach.py`
- `backend/app/providers/anthropic.py`

There are two paths:

1. deterministic fallback, always available
2. optional Claude JSON generation, only when external API calls are enabled

The deterministic version produces:

```text
Trigger → Transform → Sync → Notify → Audit
```

## Competitive Trigger

Files:

- `backend/app/providers/web_fetcher.py`
- `backend/app/core/signal_rules.py`
- `backend/app/services/competitive.py`
- `backend/app/services/outreach.py`

The scraper now checks page text, links, image alt text, and asset names for:

- Merge.dev
- Paragon / useparagon

When found, the tool changes the GTM angle to a Rutter comparison/replacement angle.

## Tests

Run:

```bash
cd backend
pytest
```

Checklist tests live in:

```text
backend/tests/test_checklist_features.py
```
