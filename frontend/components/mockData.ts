import type { CompanyProfile } from "../lib/types";

export const mockCompanies: CompanyProfile[] = [
  {
    id: "mock_1",
    name: "Monk",
    domain: "monk.ai",
    website_url: "https://monk.ai",
    one_liner: "AI vehicle inspection workflows for automotive teams.",
    category: "automotive workflow automation",
    employee_count_estimate: 80,
    likely_customer_systems: ["fleet management system", "dealer management system", "claims system"],
    integration_need_hypothesis:
      "Monk likely needs to move inspection data into fleet, dealer, and insurance claims systems.",
    evidence_summary:
      "Mentioned 'API' and 'inspection' on their website; mentioned 'fleet management' and 'claims management' on their product pages.",
    competitive_triggers: [],
    primary_persona: {
      persona: "product",
      titles: ["Head of Product", "VP Product"],
      why: "Company appears to be over 50 people, so product likely owns roadmap tradeoffs when integrations block deals.",
      priority: 5
    },
    stage: "outbound_ready",
    score: 88,
    confidence: "high",
    evidence: [
      {
        id: "ev1",
        type: "website_copy",
        source_url: "https://monk.ai",
        snippet: "API-powered inspection workflows",
        signal: "developer_surface",
        weight: 4,
        matched_keyword: "API",
        source_context: "website"
      },
      {
        id: "ev2",
        type: "website_copy",
        source_url: "https://monk.ai",
        snippet: "vehicle inspection and damage reports",
        signal: "workflow_product",
        weight: 2,
        matched_keyword: "inspection",
        source_context: "website"
      }
    ],
    signal_scores: [
      { signal: "developer_surface", points: 14, max_points: 15, reason: "API language found." },
      { signal: "integration_language", points: 13, max_points: 15, reason: "Likely sync use case." },
      { signal: "customer_system_complexity", points: 15, max_points: 15, reason: "Automotive has messy systems." }
    ],
    personas: [
      {
        persona: "product",
        titles: ["Head of Product", "VP Product"],
        why: "Product owns roadmap tradeoffs.",
        priority: 5
      }
    ],
    outreach: {
      subject: "Integration question for Monk",
      body: "Hi {{first_name}},\n\nI was looking at Monk and noticed the vehicle inspection workflow..."
    },
    demo: {
      title: "Monk → claims system integration flow",
      hypothesis: "Inspection data should sync into downstream systems.",
      steps: ["New inspection completed", "Normalize damage fields", "Push report into claims system", "Notify adjuster"],
      public_assets_needed: ["website copy", "public screenshots"],
      estimated_build_minutes: 120
    }
  },
  {
    id: "mock_2",
    name: "AcmeOps",
    domain: "acmeops.com",
    website_url: "https://acmeops.com",
    one_liner: "AI operations platform for customer workflows.",
    category: "vertical AI / workflow automation",
    employee_count_estimate: 35,
    likely_customer_systems: ["Salesforce", "NetSuite", "Slack"],
    integration_need_hypothesis:
      "AcmeOps may already understand unified integrations because public evidence mentions Paragon. Lead with a Rutter comparison angle.",
    evidence_summary:
      "Mentioned 'Paragon' on their integrations/partners page; mentioned 'NetSuite' and 'Salesforce' on their engineering job posting.",
    competitive_triggers: [
      {
        competitor: "Paragon",
        evidence_ids: ["ev3"],
        angle:
          "Competitive trigger found for Paragon. Lead with a Rutter comparison angle around coverage gaps, implementation speed, and maintenance burden.",
        risk_note: "Validate this is a real vendor/customer relationship before sending."
      }
    ],
    primary_persona: {
      persona: "founder",
      titles: ["Founder", "CEO", "Co-founder"],
      why: "Company appears to be under 50 people, so the founder is most likely to own integration tradeoffs directly.",
      priority: 5
    },
    stage: "outbound_ready",
    score: 91,
    confidence: "high",
    evidence: [
      {
        id: "ev3",
        type: "integrations_page",
        source_url: "https://acmeops.com/integrations",
        snippet: "Paragon embedded integrations",
        signal: "competitor_presence",
        weight: 5,
        matched_keyword: "Paragon",
        source_context: "integrations/partners page"
      }
    ],
    signal_scores: [{ signal: "competitor_presence", points: 10, max_points: 10, reason: "Competitor trigger found." }],
    personas: [
      {
        persona: "founder",
        titles: ["Founder", "CEO", "Co-founder"],
        why: "Founder likely owns integration tradeoffs directly.",
        priority: 5
      }
    ],
    outreach: {
      subject: "Rutter angle for AcmeOps's integrations",
      body: "Hi {{first_name}},\n\nI noticed a public signal around Paragon..."
    },
    demo: {
      title: "Rutter replacement angle: AcmeOps → Salesforce",
      hypothesis: "Show a better customer-facing integration path.",
      steps: ["Customer record created", "Map fields into Salesforce", "Sync through Rutter-style flow"],
      public_assets_needed: ["website copy", "public integration page"],
      estimated_build_minutes: 150
    }
  }
];
