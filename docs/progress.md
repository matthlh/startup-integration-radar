# Integration Scout — progress log

A long-form history of what's been built and what's open. CLAUDE.md is the at-a-glance summary; this file is the audit trail. Updated at the end of major tasks.

## Major milestones

### Phase 1–3: foundation
- `4c11dfc` — initial monorepo skeleton (backend + frontend + scripts).
- `e612ecb` — Python 3.9 compatibility (`eval_type_backport`).
- `32e8eb1` — Evidence Collector quality bump (summarize keywords + source context).
- `5e2d86e` — scoring pipeline made generic + config-driven (`signals.yaml`).
- `a46473f` — product renamed Rutter Integration Radar → **Integration Scout**.
- `32c4451` — persona rules + categories moved into `signals.yaml`.
- `369bd84` — CSV seed import.

### Phases 4–9: Clay export, summary extraction, persona rules, approval filter
Commit `c1b2d7c`. Bundled:
- ClayExportRow rebuilt to 22 stable Clay-friendly columns (later grew to 27).
- Meta description / OpenGraph / H1+H2 extraction + `company_summary` priority picker.
- Page-type-weighted category inference (homepage dominates).
- Persona routing migrated to YAML `persona_rules` block with conditions and reasons.
- `review_status` widened to `new | approved | skip | needs_research`; CLI `--status` filter; backend `?status=` filter and PATCH endpoint.
- README beginner rewrite. New `docs/EDITING_SCORING_RULES.md`.
- Bug fixes from a QA report: hypothesis re-derive after seed-CSV category override; `crawl_quality_warning`; employee-count regex tightening; misleading 100-point comment.
- Tests grew 22 → 100.

### Phase 12: Exa discovery + safe failures
Commit `4d83213`.
- `discover` CLI writes seed CSV instead of auto-analyzing.
- `--live` flag gated by `ENABLE_EXTERNAL_API_CALLS` + `EXA_API_KEY`; falls back to dry-run with a clear message.
- New `Discovery workflow` section in README.

### Phase 13: deployment plan
Discussion + `docs/DEPLOYMENT.md` written. **Nothing is deployed yet.** Targets: Vercel frontend + Railway/Render backend with mounted volume for the JSON store.

### Deployment prep
Commit `a57b65c`.
- `DATA_DIR` and `ALLOWED_ORIGINS` env vars wired through Settings; defaults preserve local-dev behavior.
- `/api/health` returns service/storage/version/external-calls flag.
- `Procfile`, `railway.json`, `nixpacks.toml`, `render.yaml` added.
- `field_validator` on `data_dir` + `allowed_origins` so blank `.env` values fall back to defaults; new `settings_ignoring_dotenv()` helper so tests don't read the developer's local `.env`.

### Dashboard polish + sidebar
Commit `17f85c8`.
- Viewport-edge **Companies sidebar** with collapsible rail and mobile drawer. Search + quick filters (All / Hot / Approved / Needs research / New). Click-to-scroll to card via `cardIdForDomain(domain)`. Active card gets a darker ring.
- Hero error banner: italic red for "domain unreachable" / "partial crawl" / "backend down".
- "Avg score" metric removed.
- Hid Next.js bottom-left dev indicator (`devIndicators: false`).

### Memory system (this session)
Uncommitted, current branch.
- New `CLAUDE.md` (under 5k tokens) covers project summary, stack, folders, run commands, hard constraints, and pointers to detail files.
- This `docs/progress.md` is the long-form history; updated at the end of each major task.
- `session_summary.md` (at repo root) holds the active-session state. Read it first; re-write it at session end.
- Detail logs no longer go in `CLAUDE.md`; they go here.

### Analysis quality: evidence-first destinations + fit_quality
Commit `64604e4`.
- New `services/destinations.py` picks branded systems found in crawl text BEFORE category default.
- `signals.yaml` gains `destination_systems` (12 verticals), `known_systems` (alias map), and `mature_platform_hints` (Notion/Slack/Linear/Airtable/Figma/…).
- `FitQuality` enum: `strong_fit | possible_fit | weak_fit | bad_fit | mature_platform`.
- `services/fit_quality.compute_fit_quality()` runs precedence: bad-domain → mature-platform → score banding. Each path emits `prospect_reasoning`.
- Bad-domain detection caps score at 20 and suppresses outreach/demo generation.
- Careers-page hits weigh 0.5× in scoring math (`HALF_WEIGHT_SOURCES`).
- `ClayExportRow` gains `fit_quality` + `prospect_reasoning` columns.
- Frontend `CompanyCard` renders fit chip + "Should we reach out?" panel.
- Seed CSV: `snapsheet.com` → `snapsheetclaims.com`. Five other rows retargeted to match new destination map.
- Tests grew to 120.

## Important commits (chronological)

| Commit | Subject |
|---|---|
| `4c11dfc` | Initial monorepo skeleton |
| `5e2d86e` | Scoring config-driven via signals.yaml |
| `a46473f` | Renamed to Integration Scout |
| `32c4451` | Personas + categories moved into signals.yaml |
| `369bd84` | CSV seed import |
| `16a1a58` | Phases 4–9 bundle (Clay export, summary, category, personas, approval) |
| `4d83213` | Phase 12: Exa discovery + safe failure |
| `c1b2d7c` | UX overhaul + QA bug fixes (100 tests) |
| `a57b65c` | Deployment prep (DATA_DIR, CORS, /api/health) |
| `17f85c8` | Sidebar + error banner + dev-indicator hide |
| `64604e4` | Evidence-driven destinations + fit_quality + careers downweight |

## Current bugs / known issues

- **Mature *vertical* SaaS not flagged.** `mature_platform_hints` covers Notion/Slack/etc. but not Samsara/Motive/ServiceTitan. Operator judges manually for now.
- **Some sites block our crawler entirely.** Artisan returned no usable pages → flagged `bad_fit` correctly, but there's no retry (e.g., trying a known `/about` URL).
- **Evidence-first picker has no relevance gate.** When the crawl finds a branded system that doesn't fit the category (e.g., Snowflake on a logistics company), it can outrank the category-default targets. Considered intentional for now.
- **Employee-count heuristic** is regex-only. Still rare unicorn-as-founder false positives possible.
- **Sidebar active state** is click-driven, not scroll-tracked. Acceptable today but worth revisiting.

## Roadmap (rough order)

1. Fallback sub-path crawling when homepage looks junky (snapsheet.com → snapsheetclaims.com class of bug).
2. Weight branded findings by category relevance so logistics doesn't lead with Snowflake.
3. Bulk-approve in the dashboard.
4. Scroll-tracked sidebar active state.
5. Document the Clay export schema in a versioned file rather than implicit `ClayExportRow`.
6. Mature-vertical-SaaS hint coverage.

## Testing history

- After Phase 7: 61 tests.
- After Phases 4–9 bundle: 100 tests.
- After Phase 12: 76 tests covering `test_discovery.py`. (Discrepancy is fine — different files counted separately.)
- After deployment prep: 110 tests.
- After analysis-quality pass: 120 tests passing (10 new in `test_analysis_quality.py`).
- Frontend: `npm run build` clean throughout.

## Open questions

- When the hosted backend ships, do we need real auth or is Vercel Access + a shared bearer token enough? Discussed in `docs/DEPLOYMENT.md`; decision deferred.
- Should the destination picker have a "score" per branded finding (frequency × source-context weight)? Right now it's first-match-wins on insertion order.
- Should the dashboard show "score history" so the operator can see what changed after re-analysis? Not done yet.
- Should `discover --live` auto-add to the queue, or always require manual review of the discovery CSV first? Currently always-review.
