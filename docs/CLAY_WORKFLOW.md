# Clay Workflow

## Export from app

```bash
cd backend
python scripts/radar.py export ../exports/clay_export.csv
```

## Import into Clay

Use the CSV as a company table.

Recommended Clay enrichments:

1. Find company LinkedIn from domain.
2. Enrich company headcount, funding, location, and description.
3. Find people by title using `suggested_titles`.
4. Prioritize Product, Partnerships, Engineering, Solutions.
5. Find work emails.
6. Validate emails.
7. Use `outreach_body` as the base personalization.

## Suggested contact search titles

- Head of Product
- VP Product
- Product Lead
- Product Manager, Integrations
- Head of Partnerships
- Ecosystem Lead
- CTO
- Head of Engineering
- Solutions Engineering Lead
- Implementation Lead

## Output columns after Clay

- contact_name
- contact_title
- contact_linkedin
- contact_email
- email_status
- company_linkedin
- headcount
- funding_stage
- location
