# Why this is improved from the AIR Fit Engine pattern

The AIR-style scaffold was mainly:

```text
scrape → extract → score → export
```

That is useful, but too thin for this GTM problem. Integration prospecting needs proof, prioritization, and follow-through.

## Improvements

### 1. Evidence-first scoring

Every signal now points back to an `Evidence` object with:

- source URL
- snippet
- signal type
- weight

This makes manual review much faster and prevents fake-confidence scores.

### 2. Pipeline stages

Companies move through stages:

```text
discovered → profiled → scored → enriched → outbound_ready → demo_ready
```

This maps to real GTM work instead of just producing a number.

### 3. Persona targeting

The app recommends who to contact:

- Product
- Partnerships
- Engineering
- Solutions
- Founder

The score alone is not enough. GTM needs the right door to knock on.

### 4. Clay handoff

The app does not try to be Clay. It exports the exact columns needed so Clay can handle contact enrichment, email verification, and company data enrichment.

### 5. Demo concept generation

For top companies, the app creates a demo angle:

```text
trigger → transform → sync → notify → audit/retry
```

This directly supports the brother's plan: if cold outbound fails, build personalized demos with Claude + Vercel.

### 6. Safer external tools

Paid tools are disabled by default.

```env
ENABLE_EXTERNAL_API_CALLS=false
```

This keeps early testing cheap and prevents accidental spend.

### 7. Agent-ready repo

`CLAUDE.md`, `AGENTS.md`, and runbooks tell Claude Code what the product is, what not to build, and how to extend it safely.
