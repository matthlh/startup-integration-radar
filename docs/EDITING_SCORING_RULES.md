# Editing scoring rules

All scoring rules live in **one file**:

```
backend/config/signals.yaml
```

You don't need to know Python to tune detection. After saving the file, re-run analysis:

```bash
python scripts/radar.py run
```

This guide covers the common edits, with examples of good and bad keywords.

---

## What's in the file

The file has five sections, in order:

1. **`your_company_name`** — used in the suggested-email templates.
2. **`signals:`** — keyword buckets used to score each company. **This is what you'll edit most.**
3. **`personas:`** — title lists, rationales, priorities, and `small_company_threshold`.
4. **`persona_rules:`** — which personas fire under which conditions.
5. **`categories:`** — verticals used to label each company.
6. **`competitors:`** — integration-platform names that trigger a comparison-style outreach angle.

---

## How scoring works (60-second version)

Each crawled page is scanned for keywords. Every hit adds points to that signal's bucket, capped at `max_points` per signal. The total score (capped at 100) is the sum of all buckets.

```yaml
signals:
  integration_language:
    max_points: 15        # cap for this bucket
    weight: 4             # multiplier when many hits accumulate
    keywords:
      - integration
      - salesforce
      - netsuite
```

The buckets sum to more than 100 on purpose — three or four strong signals saturate the cap. The `disqualifier:` bucket is the inverse: each hit subtracts 35 points so a single match dominates the cap.

---

## How to add a keyword

Find the right signal bucket, add a string to its `keywords:` list, save, re-run.

```yaml
signals:
  competitor_presence:
    max_points: 10
    weight: 5
    keywords:
      - merge.dev
      - paragon
      - workato        # ← new
```

That's it. Capitalization doesn't matter — matching is lowercased.

### Good vs. bad keywords

| ✅ Good | ❌ Bad | Why |
|---|---|---|
| `salesforce`, `hubspot`, `netsuite` | `crm` *(too generic)* | Specific brand names rarely false-positive; `crm` matches every B2B SaaS site. |
| `merge.dev`, `paragon embedded` | `merge` *(too short)* | Short common words like "merge" appear in unrelated copy ("merge requests"). The pipeline already special-cases `paragon` and `merge` to avoid this — keep keywords distinctive. |
| `we're hiring integrations engineer` | `engineer` | Multi-word phrases give context; single common nouns don't. |
| `request demo`, `book a demo` | `demo` | The single word matches "demolition" and product copy noise. |
| `procore`, `autodesk construction cloud` | `construction` | Brand names show up only when the topic is real. The single word catches blog mentions. |

Rule of thumb: if a random consumer site might use the word in passing, it's a bad keyword. If it only shows up when the company actually does this work, it's a good keyword.

### Keywords that don't fire

If you add a keyword and it doesn't seem to register, check:

1. **Whole-word matches.** Words ≤ 4 characters require a word boundary (so `api` does NOT match `napiform`). Longer words match anywhere.
2. **The `paragon` and `merge` short-circuits.** These are special-cased in `app/core/signals.py` because they're common nouns. If you need to detect a new ambiguous-name competitor, add it to `competitors:` and the pipeline will handle aliases for you.
3. **Page type.** Categories are inferred mostly from the homepage. Mentions of `procore` on a careers page count as integration evidence but don't change the company's vertical.

---

## How to change a weight or cap

```yaml
signals:
  developer_surface:
    max_points: 15      # raise the cap → this signal can contribute more
    weight: 4           # higher weight → bigger bonus when many keywords hit
    keywords:
      - api
      - apis
      - ...
```

- **`max_points`** is the per-bucket cap. Raise it to let a single signal carry more of the score.
- **`weight`** scales the bonus when the same signal fires multiple times. Useful for signals you trust (specific competitor names, named ERPs) and dangerous for noisy ones.

If you find every company is scoring 90+, lower a weight or raise the bar in your review workflow rather than deflating the cap globally.

---

## How to add a competitor trigger

Two places, both in `signals.yaml`:

```yaml
signals:
  competitor_presence:
    keywords:
      - workato

competitors:
  "Workato":
    aliases:
      - workato
      - workato embedded
      - workato integration
```

When any alias is found on a page, the company gets a `CompetitiveTrigger` and the suggested email switches to a comparison angle ("I noticed you mention Workato — rather than a generic integration pitch, I'd ask…") instead of the default integration-need pitch.

The display name (the `"Workato":` key) is what shows up in the dashboard chip and the email body. The aliases are what's actually matched in the page text — include lower-case forms.

---

## How to change persona routing

`persona_rules:` decides who shows up as primary/secondary based on size and detected signals. Each rule has a condition, a target persona, and a human-readable reason.

```yaml
persona_rules:
  primary:
    - name: small_company_founder
      condition:
        employee_count: { lt: 50 }
      persona: founder
      reason: "Company appears to have fewer than 50 employees..."

    - name: scaled_company_product
      condition:
        employee_count: { gte: 50 }
      persona: product
      reason: "Company appears to have 50+ employees..."

  secondary:
    - name: developer_surface_signal
      condition:
        any_signal: [developer_surface, implementation_burden]
      persona: engineering
      reason: "API/SDK/webhook language detected..."
```

### Condition shapes

| Shape | Example | Meaning |
|---|---|---|
| `employee_count: { lt: 50 }` | size < 50 | strictly less than |
| `employee_count: { gte: 50 }` | size ≥ 50 | greater than or equal |
| `employee_count: unknown` | — | size couldn't be inferred |
| `any_signal: [a, b, c]` | — | at least one of the signals has positive points |
| `score_lt: 70` | — | total score < 70 |
| `score_gte: 70` | — | total score ≥ 70 |

### Common edits

- **Retarget partnerships at smaller companies**: change the secondary `partnership_language_signal` rule to fire only when `employee_count: { gte: 25 }`.
- **Stop suggesting founder when score is high**: the `weak_score_founder_fallback` rule already only fires when `score_lt: 70`. Lower it to 60 if you want to keep founder out of strong leads.
- **Add a new persona**: add a block under `personas:` (with title list, why, priority) AND reference it from a `persona_rules:` rule. Both halves are needed.

After editing, re-run: `python scripts/radar.py run`.

The bucket each rule lands in (primary / secondary / fallback) is reported in the `persona_reasoning` field of the export so you can audit which rule fired.

---

## How to add a vertical (category)

```yaml
categories:
  - name: insurance claims
    keywords: [claim, claims, carrier, policyholder, fnol]
```

Categories are matched against the **homepage** only (title, meta description, headings, body), with secondary pages contributing very little weight. This is intentional — careers and integrations pages mention customer-system names (Procore, Autodesk, NetSuite) that would otherwise pull every company toward construction tech.

If a homepage doesn't match any category, the company falls back to `vertical AI / workflow automation` (when "ai" or "automation" appears) or `B2B workflow software`.

---

## How to avoid bad scoring rules

- **Don't add common words.** `software`, `platform`, `enterprise`, `tool`, `team` will fire on almost every B2B site.
- **Don't add words that are part of larger common terms.** `cs` matches "customers", "csv", "discuss". `ml` matches "html". Keep keywords ≥ 5 characters when possible, or use multi-word phrases.
- **Don't combine signals.** If you want to require both "integration" and "salesforce" to fire, that's a derived signal — it's easier to just add `salesforce` to a high-weight bucket.
- **Don't bypass the pipeline by writing rules in Python.** The whole point of `signals.yaml` is to keep this configurable. If you're tempted to special-case in code, ask first whether a new keyword bucket would do the same job.

---

## Sanity-check after editing

```bash
# Make sure the file still parses
python -c "from app.core.signal_rules import get_config; get_config()"

# Re-run a small batch and eyeball the results
python scripts/radar.py reset
python scripts/radar.py run

# Run the test suite to catch regressions
pytest
```

Bad YAML (a missing colon, wrong indentation, an unknown signal name) will fail loudly at import time — you won't analyze a single company against a broken config.
