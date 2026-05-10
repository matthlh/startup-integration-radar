import type { CompanyProfile, ReviewStatus } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api";

export async function listCompanies(): Promise<CompanyProfile[]> {
  const response = await fetch(`${API_BASE}/companies`, { cache: "no-store" });
  if (!response.ok) return [];
  return response.json();
}

export async function analyzeDomain(domain: string): Promise<CompanyProfile> {
  const response = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ domain, save: true, use_llm: false }),
  });
  if (!response.ok) throw new Error("Failed to analyze domain");
  return response.json();
}

export function clayExportUrl(status?: ReviewStatus): string {
  const base = `${API_BASE}/exports/clay.csv`;
  return status ? `${base}?status=${status}` : base;
}

export async function setReviewStatus(
  domain: string,
  reviewStatus: ReviewStatus,
): Promise<CompanyProfile> {
  const response = await fetch(`${API_BASE}/companies/${domain}/review_status`, {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ review_status: reviewStatus }),
  });
  if (!response.ok) throw new Error("Failed to update review status");
  return response.json();
}

export interface SeedRow {
  domain: string;
  company_name: string;
  category: string;
  notes: string;
}

export async function listSeeds(): Promise<SeedRow[]> {
  const response = await fetch(`${API_BASE}/seeds`, { cache: "no-store" });
  if (!response.ok) return [];
  return response.json();
}

export async function addSeed(row: Partial<SeedRow> & { domain: string }): Promise<{
  row: SeedRow;
  added: boolean;
}> {
  const response = await fetch(`${API_BASE}/seeds`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(row),
  });
  if (!response.ok) throw new Error("Failed to add seed");
  return response.json();
}

export async function removeSeed(domain: string): Promise<boolean> {
  const response = await fetch(`${API_BASE}/seeds/${encodeURIComponent(domain)}`, {
    method: "DELETE",
  });
  return response.ok;
}
