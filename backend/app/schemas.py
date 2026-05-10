from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl, field_validator


class PipelineStage(str, Enum):
    discovered = "discovered"
    profiled = "profiled"
    scored = "scored"
    enriched = "enriched"
    outbound_ready = "outbound_ready"
    demo_ready = "demo_ready"
    disqualified = "disqualified"


class Confidence(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class EvidenceType(str, Enum):
    website_copy = "website_copy"
    docs = "docs"
    integrations_page = "integrations_page"
    careers = "careers"
    funding_or_news = "funding_or_news"
    manual_note = "manual_note"
    llm_inference = "llm_inference"


class SignalName(str, Enum):
    workflow_product = "workflow_product"
    developer_surface = "developer_surface"
    integration_language = "integration_language"
    enterprise_motion = "enterprise_motion"
    customer_system_complexity = "customer_system_complexity"
    implementation_burden = "implementation_burden"
    partner_ecosystem = "partner_ecosystem"
    urgency_or_growth = "urgency_or_growth"
    demoability = "demoability"
    competitor_presence = "competitor_presence"
    disqualifier = "disqualifier"


class PersonaName(str, Enum):
    product = "product"
    partnerships = "partnerships"
    engineering = "engineering"
    solutions = "solutions"
    founder = "founder"
    revenue = "revenue"


class Evidence(BaseModel):
    id: str = Field(default_factory=lambda: f"ev_{uuid4().hex[:10]}")
    type: EvidenceType
    source_url: str = ""
    page_title: str = ""
    snippet: str
    signal: SignalName | None = None
    weight: int = Field(default=1, ge=-10, le=20)
    matched_keyword: str = ""
    source_context: str = "website"


class SignalScore(BaseModel):
    signal: SignalName
    points: int = Field(ge=-100, le=100)
    max_points: int = Field(gt=0)
    evidence_ids: list[str] = Field(default_factory=list)
    reason: str = ""


class PersonaRecommendation(BaseModel):
    persona: PersonaName
    titles: list[str]
    why: str
    priority: int = Field(default=1, ge=1, le=5)


class CompetitiveTrigger(BaseModel):
    competitor: str
    evidence_ids: list[str] = Field(default_factory=list)
    angle: str
    risk_note: str = "Validate this is a real vendor/customer relationship before sending."


class ContactPlaceholder(BaseModel):
    name: str = ""
    title: str = ""
    linkedin_url: str = ""
    email: str = ""
    persona: PersonaName | None = None
    source: str = ""
    status: Literal["needed", "found", "verified", "bounced"] = "needed"


class OutreachAsset(BaseModel):
    subject: str
    body: str
    first_line: str = ""
    call_to_action: str = ""
    risk_notes: list[str] = Field(default_factory=list)


class DemoConcept(BaseModel):
    title: str
    hypothesis: str
    steps: list[str]
    public_assets_needed: list[str] = Field(default_factory=list)
    estimated_build_minutes: int = Field(default=90, ge=10, le=480)


class CompanyProfile(BaseModel):
    id: str = Field(default_factory=lambda: f"co_{uuid4().hex[:10]}")
    name: str
    domain: str
    website_url: str
    one_liner: str = ""
    company_summary: str = ""
    company_summary_source: str = ""
    category: str = ""
    inferred_category: str = ""
    category_confidence: Confidence = Confidence.low
    category_evidence: list[str] = Field(default_factory=list)
    customer_type: str = ""
    employee_count_estimate: int | None = None
    likely_customer_systems: list[str] = Field(default_factory=list)
    integration_need_hypothesis: str = ""
    evidence_summary: str = ""
    competitive_triggers: list[CompetitiveTrigger] = Field(default_factory=list)
    primary_persona: PersonaRecommendation | None = None
    persona_reasoning: list[str] = Field(default_factory=list)
    stage: PipelineStage = PipelineStage.discovered
    score: int = Field(default=0, ge=0, le=100)
    confidence: Confidence = Confidence.low
    evidence: list[Evidence] = Field(default_factory=list)
    signal_scores: list[SignalScore] = Field(default_factory=list)
    personas: list[PersonaRecommendation] = Field(default_factory=list)
    contacts: list[ContactPlaceholder] = Field(default_factory=list)
    outreach: OutreachAsset | None = None
    demo: DemoConcept | None = None
    disqualification_reason: str = ""
    pages_fetched: list[str] = Field(default_factory=list)
    crawl_quality_warning: str = ""
    review_status: Literal["new", "approved", "skip", "needs_research"] = "new"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("domain")
    @classmethod
    def normalize_domain(cls, value: str) -> str:
        value = value.strip().lower()
        value = value.replace("https://", "").replace("http://", "")
        value = value.split("/")[0]
        if value.startswith("www."):
            value = value[4:]
        return value


class AnalyzeCompanyRequest(BaseModel):
    domain: str
    use_llm: bool = False
    save: bool = True


class AnalyzeBatchRequest(BaseModel):
    domains: list[str] = Field(min_length=1, max_length=200)
    use_llm: bool = False
    save: bool = True


class DiscoveryRequest(BaseModel):
    seed_company: str | None = None
    query: str
    limit: int = Field(default=25, ge=1, le=100)
    dry_run: bool = True


class DiscoveryCandidate(BaseModel):
    name: str
    domain: str
    url: str
    reason: str = ""
    source: str = "manual_query"


class ClayExportRow(BaseModel):
    # ── Identity ──────────────────────────────────────────────────────────
    company_name: str
    domain: str
    website_url: str
    category: str
    inferred_category: str = ""
    category_confidence: str = ""
    company_summary: str = ""
    company_summary_source: str = ""
    # ── Scoring ───────────────────────────────────────────────────────────
    score: int
    scoring_rules_version: str = ""
    scoring_profile_name: str = ""
    scoring_explanation: str = ""
    signal_score_breakdown: str = ""
    # ── Evidence ──────────────────────────────────────────────────────────
    evidence_summary: str = ""
    integration_need_hypothesis: str = ""
    # ── Personas / contacts ───────────────────────────────────────────────
    primary_persona: str = ""
    secondary_personas: str = ""
    suggested_contact_titles: str = ""
    clay_contact_search_titles: str = ""
    persona_reasoning: str = ""
    # ── Competitive context ───────────────────────────────────────────────
    competitor_or_existing_stack_trigger: str = ""
    # ── Outreach assets ───────────────────────────────────────────────────
    demo_concept: str = ""
    suggested_email_subject: str = ""
    suggested_email_body: str = ""
    # ── Provenance ────────────────────────────────────────────────────────
    source_pages_scanned: str = ""
    crawl_quality_warning: str = ""
    # ── Clay workflow ─────────────────────────────────────────────────────
    review_status: str = "new"
    notes: str = ""
