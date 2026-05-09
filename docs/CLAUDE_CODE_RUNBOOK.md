# Claude Code Runbook

## First prompt

```text
Read CLAUDE.md, PRD.md, docs/IMPLEMENTATION_PLAN.md, docs/SCORING_RUBRIC.md, and docs/OUTBOUND_PLAYBOOK.md.
Do not code yet. Summarize what this repo does, explain the current architecture, and recommend the smallest next useful task.
```

## Improve scoring prompt

```text
Improve the scoring rubric for integration-heavy B2B companies.
Add tests before changing behavior.
Focus on reducing false positives from consumer apps and agencies while keeping vertical AI/workflow SaaS high scoring.
```

## Add CSV import prompt

```text
Add a CLI command that imports domains from a CSV with columns name,domain,reason and analyzes them in batch.
Keep the existing JSON store.
Add tests if practical.
```

## Frontend prompt

```text
Use docs/FIGMA_MAKE_HANDOFF.md as the product/design spec.
Improve the dashboard so a user can review 100 companies quickly.
Add filters, evidence details, and clearer pipeline status.
Do not add auth or complex state libraries.
```

## Demo generator prompt

```text
Add a demo brief export for the top 10 companies by score.
Each brief should include company context, likely customer system, integration flow, needed public assets, and a Vercel/Claude prompt.
```
