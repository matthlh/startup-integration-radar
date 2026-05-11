# Session summary

Read this first at the start of every Claude Code session. Re-write it at session end.

## What changed this session

1. **CLAUDE.md** rewritten to a tighter, under-5k-token version. Removed obsolete pointers to files that didn't exist; trimmed historical detail; added a `Hard constraints` block and a `Current top priorities` block that points at this file.
2. **docs/progress.md** created. Long-form history of every commit + phase + bug + open question, so CLAUDE.md doesn't have to carry it.
3. **session_summary.md** created (this file).

No backend code, frontend code, schemas, configs, or tests changed this session.

## Branch / commit

- Branch: `main`
- Last commit on `origin/main`: **`64604e4`** — "Evidence-driven destination systems, fit_quality, careers downweight"
- Working tree currently has uncommitted: `CLAUDE.md`, `docs/progress.md`, this file.

## Tests run

- None this session. The last committed state is verified green: backend `pytest -q` → **120 passed**; frontend `npm run build` → ✓ clean.

## Remaining bugs / known issues (carried forward)

1. Mature *vertical* SaaS (Samsara, Motive, ServiceTitan) doesn't auto-downgrade to `mature_platform`; operator judges manually. Hint list only covers horizontal SaaS.
2. Sites that block our crawler (e.g. Artisan) correctly land at `bad_fit` but there's no retry against a known sub-path (e.g. `/about`).
3. Evidence-first destination picker has no category-relevance gate. A logistics company can lead with "Snowflake" if it's the first branded system found.
4. Employee-count heuristic is regex-only — rare unicorn-as-founder false positives still possible.
5. Sidebar active state is click-driven, not scroll-tracked.
6. No bulk-approve flow in the dashboard.
7. **UX/trust pass deferred (see below).** Cards still labeled "Add to seed list" / "Analyze now"; dashboard has no visible queue panel and no "Analyze all queued"; card sections aren't collapsible; sort dropdown is missing.

## Exact recommended next prompt

Paste this as your first message in the next session:

> We are doing the deferred UX + trust pass on Integration Scout. Goal: make the dashboard clearer, less redundant, and more trustworthy.
>
> Inspect only:
> - frontend/app/page.tsx
> - frontend/components/CompanyCard.tsx
> - frontend/components/CompanySidebar.tsx
> - frontend/lib/api.ts
> - frontend/lib/types.ts
> - backend/app/api/routes.py
> - backend/app/services/profiler.py
> - backend/config/signals.yaml
>
> Acceptance criteria:
> 1. Rename user-facing "seed list" → "queue" everywhere (UI text only; keep backend names).
> 2. Replace the hero's two buttons with three: **Add to queue**, **Analyze this company**, **Analyze all queued**. Keep **Export approved** in the corner.
> 3. Add a visible **Company Queue** panel/drawer showing rows from `GET /api/seeds` with per-row "Analyze this" + remove buttons.
> 4. Add `POST /api/analyze/queue` that iterates the seed CSV, profiles each row, applies seed-CSV name/category overrides, calls `refresh_derived_fields` for category-overridden rows, and returns `{ analyzed, failed, results: [...] }`.
> 5. Wire the dashboard to that endpoint with a progress indicator.
> 6. Restructure `CompanyCard` so the always-visible header is: name + domain + score + fit chip + review status + summary + prospect_reasoning + evidence_summary. Move Persona, Demo, Email body, and Signal breakdown into collapsible sections.
> 7. Add a sort dropdown with: score↓ (default), score↑, A–Z, review status, fit quality. Default order: `strong_fit > possible_fit > weak_fit > mature_platform > bad_fit`, ties broken by score desc.
> 8. Preserve all existing CLI commands and tests.
> 9. Run `pytest -q` (backend) + `npm run build` (frontend). Add a backend test for the new `/api/analyze/queue` happy + empty-queue paths.
> 10. At the end: update `docs/progress.md` + `session_summary.md`, report files changed, test results, and remaining issues.
>
> Hard constraints: local-first, no deploy, no auth, no paid APIs, no email send, no big rewrites. Small focused commit at the end.

## Known pitfalls for next session

- The card already has fit_quality + prospect_reasoning rendered — don't duplicate. The work is restructuring (collapse persona/demo/email/breakdown) + clearer header order, not adding fit fields.
- `services/seed_manager.py` already provides `list_seeds()` / `add_seed()` / `remove_seed()` — reuse from the new `/api/analyze/queue` endpoint, do not re-implement.
- The sidebar's `cardIdForDomain()` helper is the existing scroll-target convention — re-use it in any new queue→card links so they all behave consistently.
- `signals.yaml` is the only source of truth for keywords, categories, personas, destination systems, and competitors. Don't hardcode anything in Python.
- `refresh_derived_fields(profile)` in `services/profiler.py` re-runs hypothesis/outreach/demo after a category override. Call it from `/api/analyze/queue` when `seed.category` differs from the inferred category — same pattern as `scripts/radar.py::analyze_csv`.
- The Snapsheet/Artisan results are baked-in expected behavior of the current pipeline. Don't try to "fix" them in this UX pass.

## Files most relevant for next session

- `frontend/app/page.tsx` — the page layout including hero, sidebar wiring, sort/filter UI.
- `frontend/components/CompanyCard.tsx` — the card to restructure with collapsibles.
- `frontend/components/CompanySidebar.tsx` — already has search + filters; integrate sort here or in page.tsx.
- `frontend/lib/api.ts` — add `analyzeQueue()` client call.
- `frontend/lib/types.ts` — types for the new endpoint's response.
- `backend/app/api/routes.py` — add the `/analyze/queue` endpoint.
- `backend/app/services/profiler.py` — for the `refresh_derived_fields` pattern.
- `backend/scripts/radar.py::analyze_csv` — reference implementation for "iterate seeds + apply overrides + refresh derived fields".
