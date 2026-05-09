# Figma Make Handoff

Use this document when generating the UI prototype.

## Product

Rutter Integration Radar is a GTM review dashboard for finding companies likely to need customer-facing integrations.

## Main screen

Create a clean SaaS dashboard with:

1. Hero/search area
   - Input for domain or seed query
   - Analyze button
   - Export Clay CSV button

2. Metrics row
   - Companies analyzed
   - Outbound ready
   - Average score
   - Top score

3. Prospect queue
   - Company cards sorted by score
   - Score badge
   - Confidence badge
   - Stage badge
   - Category
   - Integration hypothesis
   - Likely customer systems
   - Suggested persona
   - Demo angle

4. Evidence drawer/modal
   - Source URL
   - Signal type
   - Snippet
   - Weight

5. Filters
   - Score range
   - Stage
   - Category
   - Confidence

## Visual style

- Serious but modern GTM tool
- High information density without feeling like a spreadsheet swamp
- Rounded cards, neutral colors, strong typography
- Use subtle status colors but avoid neon chaos

## Design prompt for Figma Make

```text
Design a responsive SaaS dashboard for “Rutter Integration Radar,” a GTM tool that finds B2B software companies with likely integration pain.

The UI should show a pipeline from discovered companies to outbound-ready prospects. Each company card must include score, confidence, stage, integration need hypothesis, evidence snippets, suggested buyer persona, and demo concept.

Make it feel like a premium internal GTM command center. Use a clean neutral palette, rounded cards, compact filters, and clear review actions: Approve, Reject, Needs Research, Export.

Create desktop-first layout with a responsive mobile version.
```
