# PRD: Integration Scout

## Goal

Build a lightweight GTM tool that identifies B2B software companies likely to need integrations built out as part of their product, prioritizes them using public evidence, and prepares outbound and demo concepts for the highest-fit prospects.

## Primary user

A founder, GTM engineer, or integration services team looking for companies where customer-facing integrations are a clear product gap.

## Core job

Given a seed company like monk.ai, find more companies where customer integrations are likely a pain point, then create enough context to outbound intelligently.

## Non-goals

- Do not build a full CRM.
- Do not replace Clay for contact enrichment.
- Do not send emails from this app.
- Do not make paid API calls unless explicitly enabled.
- Do not over-optimize UI before validating the outbound motion.

## Key workflows

### 1. Analyze company

Input: `monk.ai`

Output:

- score
- confidence
- public evidence snippets
- likely customer systems
- buyer personas
- outreach email
- demo concept

### 2. Build target list

Input: search query or seed company

Output:

- candidate domains
- reasons for inclusion
- ability to batch analyze

### 3. Export to Clay

Output CSV columns must support:

- contact enrichment
- title/persona targeting
- email personalization
- status tracking

### 4. Demo planning

For top companies, generate a mini product demo concept:

```text
Company workflow trigger
→ transform data
→ sync into customer system
→ notification
→ audit/retry/error handling
```

## Success metrics

- 100 qualified companies found
- 70%+ of high-score companies are plausible integration prospects after manual review
- 1-2 relevant contacts per company found in Clay
- 10 custom outbound emails sent
- 2 demo concepts converted into Vercel prototypes

## Scoring philosophy

A company is attractive if it sells workflow software and its customers likely need it connected to existing systems.

Strong signals:

- API/docs/webhooks
- integrations page
- enterprise/SOC2/implementation language
- CRM/ERP/fleet/claims/project-management references
- vertical industry with messy systems
- clear workflow object that can be synced

Negative signals:

- consumer-only app
- media/newsletter
- agency or consulting-only business
- local service business

## V1 acceptance criteria

### Evidence Collector

The API response for a company must include `evidence_summary`.

Good output:

```text
Mentioned 'NetSuite' and 'QuickBooks' on their engineering job posting.
```

### Persona Logic

```text
< 50 people → Founder / CEO / Co-founder
> 50 people → Head of Product / VP Product, with Partnerships as secondary
```

### Demo Concept Generator

The product must generate a specific demo concept that can become a small prototype.

Good output:

```text
Show inspection data syncing directly into an insurance claims dashboard.
```

### Competitive Trigger

Detect integration platform signals (Merge.dev, Paragon, etc.) in page text, links, image alt text, and asset names. If found, use a comparison angle in outbound and demo copy.
