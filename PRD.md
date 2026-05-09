# PRD: Rutter Integration Radar

## Goal

Build a lightweight GTM product that identifies B2B software companies likely to need integrations, prioritizes them using public evidence, and prepares outbound/demos for the highest-fit prospects.

## Primary user

A founder or GTM engineer selling integration implementation, embedded integrations, workflow automation, or connector-building services.

## Core job

Given a seed company like Monk, find more companies where customer integrations are likely a pain point, then create enough context to outbound intelligently.

## Non-goals

- Do not build a full CRM.
- Do not replace Clay for contact enrichment.
- Do not send emails from this app yet.
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

A company is attractive if it sells workflow software and customers likely need it to connect to existing systems.

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

The repo must satisfy these concrete product checks:

### Evidence Collector

The API response for a company must include `evidence_summary`.

Good output:

```text
Mentioned 'NetSuite' and 'QuickBooks' on their engineering job posting.
```

Bad output:

```text
Score: 80
```

### Persona Logic

The product must choose a target persona based on estimated company size:

```text
< 50 people → Founder / CEO / Co-founder
> 50 people → Head of Product / VP Product, with Partnerships as secondary
```

### Demo Concept Generator

The product must generate a specific demo concept that can become a small Vercel prototype.

Good output:

```text
Show Rutter syncing automotive inspection data directly into an insurance claims dashboard.
```

### Competitive Trigger

The scraper must look for competitor signals such as Merge.dev or Paragon in:

- visible page text
- links
- image alt text
- asset names

If found, the outbound angle should become a Rutter comparison angle instead of a generic integration pitch.
