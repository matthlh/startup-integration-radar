"use client";

import { useState } from "react";
import type { CompanyProfile, ReviewStatus } from "../lib/types";

function confidenceLabel(score: number) {
  if (score >= 80) return "Hot";
  if (score >= 60) return "Warm";
  return "Watch";
}

const REVIEW_OPTIONS: { value: ReviewStatus; label: string; tone: string }[] = [
  { value: "approved", label: "Approve", tone: "bg-emerald-500 text-white" },
  { value: "needs_research", label: "Needs research", tone: "bg-amber-500 text-white" },
  { value: "skip", label: "Reject", tone: "bg-rose-500 text-white" },
];

export function CompanyCard({
  company,
  onChangeReviewStatus,
}: {
  company: CompanyProfile;
  onChangeReviewStatus?: (domain: string, status: ReviewStatus) => Promise<void> | void;
}) {
  const topPersona = company.primary_persona ?? company.personas?.[0];
  const trigger = company.competitive_triggers?.[0];
  const reviewStatus: ReviewStatus = (company.review_status as ReviewStatus) ?? "new";
  const [showEmail, setShowEmail] = useState(false);
  const [pending, setPending] = useState(false);

  async function handleReviewClick(status: ReviewStatus) {
    if (!onChangeReviewStatus) return;
    setPending(true);
    try {
      await onChangeReviewStatus(company.domain, status);
    } finally {
      setPending(false);
    }
  }

  const allTitles = Array.from(
    new Set([
      ...(topPersona?.titles ?? []),
      ...company.personas?.flatMap((p) => p.titles) ?? [],
    ]),
  );
  const secondaries = (company.personas ?? [])
    .filter((p) => p.persona !== topPersona?.persona)
    .map((p) => p.persona);

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-lg font-semibold text-slate-950">{company.name}</h3>
            <ReviewBadge status={reviewStatus} />
            <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700">
              {company.stage}
            </span>
            {trigger ? (
              <span className="rounded-full bg-amber-100 px-2 py-1 text-xs font-semibold text-amber-800">
                Competitive trigger: {trigger.competitor}
              </span>
            ) : null}
            {company.crawl_quality_warning ? (
              <span
                className="rounded-full bg-rose-100 px-2 py-1 text-xs font-semibold text-rose-800"
                title={company.crawl_quality_warning}
              >
                Crawl warning
              </span>
            ) : null}
          </div>
          <a href={company.website_url} className="text-sm text-slate-500" target="_blank" rel="noreferrer">
            {company.domain}
          </a>
          <div className="mt-1 flex flex-wrap gap-3 text-xs text-slate-500">
            <span>
              Category: <span className="font-medium text-slate-700">{company.category}</span>
              {company.category_confidence ? ` (${company.category_confidence})` : ""}
            </span>
            {company.employee_count_estimate ? (
              <span>~{company.employee_count_estimate} people</span>
            ) : null}
          </div>
        </div>
        <div className="text-right">
          <div className="text-3xl font-bold text-slate-950">{company.score}</div>
          <div className="text-xs uppercase tracking-wide text-slate-500">{confidenceLabel(company.score)}</div>
        </div>
      </div>

      {company.company_summary ? (
        <p className="mt-3 text-sm italic leading-6 text-slate-600">"{company.company_summary}"</p>
      ) : null}

      <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3">
        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Why this company needs integrations</div>
        <p className="mt-1 text-sm leading-6 text-slate-700">{company.integration_need_hypothesis}</p>
      </div>

      <div className="mt-3 rounded-xl border border-slate-200 bg-slate-50 p-3">
        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Evidence summary</div>
        <p className="mt-1 text-sm leading-6 text-slate-700">
          {company.evidence_summary || "No strong public integration evidence found yet."}
        </p>
      </div>

      {company.crawl_quality_warning ? (
        <div className="mt-3 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
          <span className="font-semibold">Crawl warning:</span> {company.crawl_quality_warning}
        </div>
      ) : null}

      <div className="mt-4 flex flex-wrap gap-2">
        {company.likely_customer_systems.slice(0, 4).map((system) => (
          <span key={system} className="rounded-full border border-slate-200 px-3 py-1 text-xs text-slate-700">
            {system}
          </span>
        ))}
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-2">
        <div className="rounded-xl bg-slate-50 p-3">
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Suggested persona</div>
          <div className="mt-1 text-sm font-medium text-slate-900">{topPersona?.persona ?? "product"}</div>
          <p className="mt-1 text-xs text-slate-600">
            {topPersona?.why ?? "Validate integration pain and roadmap priority."}
          </p>
          {allTitles.length > 0 ? (
            <p className="mt-2 text-xs text-slate-500">
              Titles to search in Clay: <span className="text-slate-700">{allTitles.slice(0, 4).join("; ")}</span>
            </p>
          ) : null}
          {secondaries.length > 0 ? (
            <p className="mt-1 text-xs text-slate-400">
              Secondary: {secondaries.join(", ")}
            </p>
          ) : null}
        </div>
        <div className="rounded-xl bg-slate-50 p-3">
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Demo concept</div>
          <div className="mt-1 text-sm font-medium text-slate-900">{company.demo?.title ?? "—"}</div>
          {company.demo?.steps?.length ? (
            <ul className="mt-2 list-disc space-y-1 pl-4 text-xs text-slate-600">
              {company.demo.steps.slice(0, 3).map((step, i) => (
                <li key={i}>{step}</li>
              ))}
            </ul>
          ) : (
            <p className="mt-1 text-xs text-slate-500">No demo concept yet — analysis may not have hit threshold.</p>
          )}
        </div>
      </div>

      {company.outreach ? (
        <div className="mt-4 rounded-xl border border-slate-200 bg-white p-3">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Suggested email</div>
              <div className="mt-1 text-sm font-semibold text-slate-900">{company.outreach.subject}</div>
            </div>
            <button
              type="button"
              onClick={() => setShowEmail((v) => !v)}
              className="rounded-lg border border-slate-200 px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50"
            >
              {showEmail ? "Hide body" : "Show body"}
            </button>
          </div>
          {showEmail ? (
            <pre className="mt-3 whitespace-pre-wrap rounded-lg bg-slate-50 p-3 text-xs leading-5 text-slate-700">
              {company.outreach.body}
            </pre>
          ) : null}
        </div>
      ) : (
        <div className="mt-4 rounded-xl border border-dashed border-slate-200 p-3 text-xs text-slate-500">
          No suggested email yet. Outreach is generated for companies scoring ≥55.
        </div>
      )}

      {onChangeReviewStatus ? (
        <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-slate-100 pt-4">
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Review</span>
          {REVIEW_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => handleReviewClick(option.value)}
              disabled={pending}
              className={`rounded-lg px-3 py-1 text-xs font-semibold disabled:opacity-50 ${
                reviewStatus === option.value ? option.tone : "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
              }`}
            >
              {option.label}
            </button>
          ))}
          <button
            type="button"
            onClick={() => handleReviewClick("new")}
            disabled={pending}
            className="ml-auto rounded-lg border border-slate-200 px-3 py-1 text-xs text-slate-500 hover:bg-slate-50 disabled:opacity-50"
          >
            Reset
          </button>
        </div>
      ) : null}
    </article>
  );
}

function ReviewBadge({ status }: { status: ReviewStatus }) {
  const map: Record<ReviewStatus, { label: string; tone: string }> = {
    approved: { label: "Approved", tone: "bg-emerald-100 text-emerald-800" },
    needs_research: { label: "Needs research", tone: "bg-amber-100 text-amber-800" },
    skip: { label: "Rejected", tone: "bg-rose-100 text-rose-800" },
    new: { label: "New", tone: "bg-slate-100 text-slate-600" },
  };
  const { label, tone } = map[status] ?? map.new;
  return <span className={`rounded-full px-2 py-1 text-xs font-semibold ${tone}`}>{label}</span>;
}
