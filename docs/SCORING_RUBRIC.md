# Scoring Rubric

The score estimates whether a company is worth outbounding for integration work.

## Max score: 100

| Signal | Max | Why it matters |
|---|---:|---|
| Workflow product | 15 | Integrations matter most when there is an actual business workflow. |
| Developer surface | 15 | APIs/docs/webhooks suggest customers or partners need to connect. |
| Integration language | 15 | Direct mention of integrations, sync, import/export, or named tools. |
| Enterprise motion | 10 | Enterprise buyers often require custom system connections. |
| Customer system complexity | 15 | CRM/ERP/DMS/EHR/TMS/etc. create integration pain. |
| Implementation burden | 10 | Onboarding/professional services imply bespoke setup work. |
| Partner ecosystem | 5 | Partners/marketplaces imply external system dependencies. |
| Urgency/growth | 5 | Funding/hiring/growth can increase integration backlog. |
| Demoability | 10 | A clear workflow object makes custom demos easier. |

## Confidence

High confidence requires:

- score >= 75
- at least 3 strong signals among workflow, developer surface, integration language, and customer system complexity

Medium confidence requires:

- score >= 55
- at least 2 strong signals

Low confidence means either weak evidence or low score.

## Disqualifiers

Subtract heavily or disqualify when the company is likely:

- consumer-only
- newsletter/media
- mobile game
- local services
- agency-only
- ecommerce store

## How to improve the rubric

All keywords, weights, and max_points are in `backend/config/signals.yaml`. Edit that file to tune scoring — no Python needed.

Add test cases in `backend/tests/` when you make significant changes.

Good test cases:

- Monk-style automotive inspection workflow (should score 75+)
- Construction tech needing Procore/Autodesk sync (should score 75+)
- Sales AI needing CRM sync (should score 70+)
- Consumer mobile app with no B2B workflow (should score < 45, disqualified)
- Pure agency with no software product (should score < 45)

## Competitive trigger scoring

A competitor signal is a positive GTM trigger — it means the company already cares about integrations.

Examples of competitors to detect (configurable in `signals.yaml`):

- Merge.dev / Merge API
- Paragon / useparagon
- Any other integration platform you add to `competitors:` in the config

If found, add `competitor_presence` evidence and generate a `competitive_triggers[]` entry.

The outreach angle should change from:

```text
Do you need integrations?
```

to:

```text
You may already care about integrations. Where is the current approach still creating coverage, speed, or maintenance gaps?
```
