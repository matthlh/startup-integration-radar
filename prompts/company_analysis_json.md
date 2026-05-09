# Company analysis JSON prompt

You are analyzing a B2B company for integration GTM fit.

Return strict JSON only:

```json
{
  "one_liner": "",
  "category": "",
  "customer_type": "",
  "likely_customer_systems": [""],
  "integration_need_hypothesis": "",
  "best_personas": [
    {
      "persona": "product|partnerships|engineering|solutions|founder|revenue",
      "titles": [""],
      "why": "",
      "priority": 1
    }
  ],
  "outreach": {
    "subject": "",
    "body": ""
  },
  "demo": {
    "title": "",
    "hypothesis": "",
    "steps": [""],
    "public_assets_needed": [""]
  },
  "risks": [""]
}
```

Rules:

- Do not overclaim.
- Use public evidence only.
- Prefer concrete systems over generic “integrations”.
- Make the outreach short and conversational.
- The demo should be buildable as a small Vercel prototype.
