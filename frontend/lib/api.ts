import type { CompanyProfile } from "./types";

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

export function clayExportUrl(status?: "approved" | "skip" | "new"): string {
  const base = `${API_BASE}/exports/clay.csv`;
  return status ? `${base}?status=${status}` : base;
}

export async function setReviewStatus(
  domain: string,
  reviewStatus: "new" | "approved" | "skip",
): Promise<CompanyProfile> {
  const response = await fetch(`${API_BASE}/companies/${domain}/review_status`, {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ review_status: reviewStatus }),
  });
  if (!response.ok) throw new Error("Failed to update review status");
  return response.json();
}
