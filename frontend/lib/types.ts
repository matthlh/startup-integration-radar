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

export interface CompanyProfile {
  id: string;
  name: string;
  domain: string;
  website_url: string;
  one_liner: string;
  category: string;
  employee_count_estimate?: number | null;
  likely_customer_systems: string[];
  integration_need_hypothesis: string;
  evidence_summary: string;
  competitive_triggers: CompetitiveTrigger[];
  primary_persona?: PersonaRecommendation | null;
  stage: PipelineStage;
  score: number;
  confidence: Confidence;
  evidence: Evidence[];
  signal_scores: SignalScore[];
  personas: PersonaRecommendation[];
  outreach?: OutreachAsset;
  demo?: DemoConcept;
}
