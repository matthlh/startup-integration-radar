import type { CompanyProfile } from "../lib/types";

function confidenceLabel(score: number) {
  if (score >= 80) return "Hot";
  if (score >= 60) return "Warm";
  return "Watch";
}

export function CompanyCard({ company }: { company: CompanyProfile }) {
  const topPersona = company.primary_persona ?? company.personas[0];
  const trigger = company.competitive_triggers?.[0];
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-lg font-semibold text-slate-950">{company.name}</h3>
            <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700">{company.stage}</span>
            {trigger ? (
              <span className="rounded-full bg-amber-100 px-2 py-1 text-xs font-semibold text-amber-800">
                Competitive trigger: {trigger.competitor}
              </span>
            ) : null}
          </div>
          <a href={company.website_url} className="text-sm text-slate-500" target="_blank">
            {company.domain}
          </a>
          {company.employee_count_estimate ? (
            <div className="mt-1 text-xs text-slate-500">Estimated size: {company.employee_count_estimate} people</div>
          ) : null}
        </div>
        <div className="text-right">
          <div className="text-3xl font-bold text-slate-950">{company.score}</div>
          <div className="text-xs uppercase tracking-wide text-slate-500">{confidenceLabel(company.score)}</div>
        </div>
      </div>

      <p className="mt-4 text-sm leading-6 text-slate-700">{company.integration_need_hypothesis}</p>

      <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3">
        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Evidence summary</div>
        <p className="mt-1 text-sm leading-6 text-slate-700">
          {company.evidence_summary || "No strong public integration evidence found yet."}
        </p>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {company.likely_customer_systems.slice(0, 3).map((system) => (
          <span key={system} className="rounded-full border border-slate-200 px-3 py-1 text-xs text-slate-700">
            {system}
          </span>
        ))}
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-2">
        <div className="rounded-xl bg-slate-50 p-3">
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Best persona</div>
          <div className="mt-1 text-sm font-medium text-slate-900">{topPersona?.titles?.[0] ?? "Head of Product"}</div>
          <p className="mt-1 text-xs text-slate-600">{topPersona?.why ?? "Validate integration pain and roadmap priority."}</p>
        </div>
        <div className="rounded-xl bg-slate-50 p-3">
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Demo angle</div>
          <div className="mt-1 text-sm font-medium text-slate-900">{company.demo?.title ?? "Integration flow demo"}</div>
          <p className="mt-1 text-xs text-slate-600">{company.demo?.steps?.[0] ?? "Show a trigger, transform, sync, and error handling loop."}</p>
        </div>
      </div>
    </article>
  );
}
