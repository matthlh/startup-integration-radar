# Outbound Playbook

## Core thesis

The outbound should not say "we build integrations" in a generic way.

It should say:

> "I noticed your workflow likely needs to connect into these customer systems. Is that becoming a blocker?"

## Best personas

1. Head of Product / VP Product
2. Head of Partnerships / Ecosystem
3. CTO / Head of Engineering
4. Head of Solutions / Implementation
5. Founder, for small companies

## Good email structure

```text
Hi {{first_name}},

I was looking at {{company}} and noticed you help {{customer_type}} with {{workflow}}.

Curious if customers ever ask to connect {{company}} into systems like {{system_1}}, {{system_2}}, or {{system_3}}?

The reason I ask is that we help teams build and maintain customer-facing integrations when they become a blocker for onboarding, enterprise deals, or implementation bandwidth.

Based on your workflow, I could imagine customers wanting:
- {{specific_sync_1}}
- {{specific_sync_2}}
- {{specific_sync_3}}

Worth a quick conversation to compare notes on where integrations are slowing things down?
```

## Follow-up with demo

If they do not respond, send a small demo concept:

```text
I mocked up a simple flow for how {{company}} could sync {{workflow_object}} into {{system}}.

Not sure if this is exactly how customers ask for it, but it seemed like a plausible integration pattern based on your product.
```

## What not to do

- Do not pretend to know their internal roadmap.
- Do not claim they have integration pain unless evidence is strong.
- Do not send a wall of text.
- Do not mention scraping/crawling in outbound.

## Competitive trigger outbound

Use this when `competitive_triggers[]` is not empty.

Subject:

```text
Integration angle for {{Company}}
```

Body skeleton:

```text
Hi {{first_name}},

I noticed a public signal around {{Competitor}}, so I'm guessing your team may already be thinking seriously about embedded or customer-facing integrations.

Rather than a generic "do you need integrations?" note, I had a more specific question: are there customer-requested systems where coverage, implementation speed, or maintenance still creates friction?

A demo for {{Company}} could show:
- a customer record/event from {{Company}} normalized into {{Customer System}}
- sync status, retries, and field mappings visible to the customer
- a path to launch more integrations without pulling core product engineers off roadmap

Worth comparing notes on where your current integration approach is working well versus where customers still ask for more?
```

Risk note: verify the competitor signal is real before high-volume sending. A logo or keyword can be incidental.
