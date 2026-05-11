export type Confidence = "low" | "medium" | "high";
export type PipelineStage =
  | "discovered"
  | "profiled"
  | "scored"
  | "enriched"
  | "outbound_ready"
  | "demo_ready"
  | "disqualified";

export interface Evidence {
  id: string;
  type: string;
  source_url: string;
  page_title?: string;
  snippet: string;
  signal?: string;
  weight: number;
  matched_keyword?: string;
  source_context?: string;
}

export interface SignalScore {
  signal: string;
  points: number;
  max_points: number;
  reason: string;
}

export interface PersonaRecommendation {
  persona: string;
  titles: string[];
  why: string;
  priority: number;
}

export interface CompetitiveTrigger {
  competitor: string;
  evidence_ids: string[];
  angle: string;
  risk_note: string;
}

export interface OutreachAsset {
  subject: string;
  body: string;
}

export interface DemoConcept {
  title: string;
  hypothesis: string;
  steps: string[];
  public_assets_needed?: string[];
  estimated_build_minutes?: number;
}

export type ReviewStatus = "new" | "approved" | "skip" | "needs_research";

export interface CompanyProfile {
  id: string;
  name: string;
  domain: string;
  website_url: string;
  one_liner: string;
  company_summary?: string;
  company_summary_source?: string;
  category: string;
  inferred_category?: string;
  category_confidence?: Confidence;
  category_evidence?: string[];
  employee_count_estimate?: number | null;
  likely_customer_systems: string[];
  integration_need_hypothesis: string;
  evidence_summary: string;
  crawl_quality_warning?: string;
  pages_fetched?: string[];
  competitive_triggers: CompetitiveTrigger[];
  primary_persona?: PersonaRecommendation | null;
  persona_reasoning?: string[];
  stage: PipelineStage;
  score: number;
  confidence: Confidence;
  evidence: Evidence[];
  signal_scores: SignalScore[];
  personas: PersonaRecommendation[];
  outreach?: OutreachAsset;
  demo?: DemoConcept;
  review_status?: ReviewStatus;
}
