from __future__ import annotations

from app.schemas import EvidenceType, SignalName

SIGNAL_MAX_POINTS: dict[SignalName, int] = {
    SignalName.workflow_product: 15,
    SignalName.developer_surface: 15,
    SignalName.integration_language: 15,
    SignalName.enterprise_motion: 10,
    SignalName.customer_system_complexity: 15,
    SignalName.implementation_burden: 10,
    SignalName.partner_ecosystem: 5,
    SignalName.urgency_or_growth: 5,
    SignalName.demoability: 10,
    SignalName.competitor_presence: 10,
    SignalName.disqualifier: 100,
}

SIGNAL_KEYWORDS: dict[SignalName, list[str]] = {
    SignalName.workflow_product: [
        "workflow", "automate", "automation", "operations", "platform", "dashboard",
        "review", "approval", "claim", "inspection", "quote", "order", "case", "ticket",
        "dispatch", "onboarding", "implementation", "process",
    ],
    SignalName.developer_surface: [
        "api", "apis", "sdk", "developer", "developers", "docs", "documentation",
        "webhook", "webhooks", "sandbox", "endpoint", "graphql", "rest api",
    ],
    SignalName.integration_language: [
        "integration", "integrations", "connect", "connected", "sync", "import", "export",
        "push data", "pull data", "salesforce", "hubspot", "slack", "sap", "netsuite",
        "quickbooks", "workday", "snowflake", "jira", "procore", "autodesk", "stripe",
    ],
    SignalName.enterprise_motion: [
        "enterprise", "security", "soc 2", "sso", "role-based", "rbac", "audit",
        "implementation", "procurement", "compliance", "customers", "case study",
    ],
    SignalName.customer_system_complexity: [
        "erp", "crm", "dms", "dealer management", "claims management", "fleet management",
        "transportation management", "warehouse", "ehr", "emr", "billing", "accounting",
        "procurement", "project management", "data warehouse", "legacy system",
    ],
    SignalName.implementation_burden: [
        "custom", "customize", "configure", "implementation", "migration", "onboarding",
        "professional services", "solution engineer", "customer success", "deployment", "rollout",
    ],
    SignalName.partner_ecosystem: [
        "partner", "partners", "marketplace", "app marketplace", "ecosystem", "reseller",
        "technology partner", "solution partner",
    ],
    SignalName.urgency_or_growth: [
        "series a", "series b", "hiring", "we're hiring", "scale", "growing", "launched",
        "new funding", "backed by", "yc", "a16z", "sequoia", "founders fund",
    ],
    SignalName.demoability: [
        "demo", "request demo", "book a demo", "case study", "customer story", "use case",
        "before and after", "template", "example", "sample", "calculator", "report",
    ],
    SignalName.competitor_presence: [
        "merge.dev", "merge api", "merge unified api", "useparagon", "paragon",
        "paragon embedded", "paragon integration", "unified api provider",
    ],
    SignalName.disqualifier: [
        "consumer app", "mobile game", "media company", "newsletter", "agency only", "consulting only",
        "ecommerce store", "restaurant", "local service", "personal blog",
    ],
}

SIGNAL_WEIGHTS: dict[SignalName, int] = {
    SignalName.workflow_product: 2,
    SignalName.developer_surface: 4,
    SignalName.integration_language: 4,
    SignalName.enterprise_motion: 2,
    SignalName.customer_system_complexity: 3,
    SignalName.implementation_burden: 2,
    SignalName.partner_ecosystem: 2,
    SignalName.urgency_or_growth: 1,
    SignalName.demoability: 2,
    SignalName.competitor_presence: 5,
    SignalName.disqualifier: -10,
}

KEYWORD_EVIDENCE_TYPE: dict[SignalName, EvidenceType] = {
    SignalName.developer_surface: EvidenceType.docs,
    SignalName.integration_language: EvidenceType.integrations_page,
    SignalName.urgency_or_growth: EvidenceType.funding_or_news,
    SignalName.competitor_presence: EvidenceType.integrations_page,
}
