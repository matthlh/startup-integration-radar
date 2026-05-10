"use client";

import { useEffect, useMemo, useState } from "react";
import {
  addSeed,
  analyzeDomain,
  clayExportUrl,
  listCompanies,
  setReviewStatus as apiSetReviewStatus,
} from "../lib/api";
import type { CompanyProfile, ReviewStatus } from "../lib/types";
import { CompanyCard } from "../components/CompanyCard";

type ReviewFilter = "all" | ReviewStatus;

export default function Home() {
  const [companies, setCompanies] = useState<CompanyProfile[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [domain, setDomain] = useState("");
  const [name, setName] = useState("");
  const [adding, setAdding] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [stageFilter, setStageFilter] = useState("all");
  const [reviewFilter, setReviewFilter] = useState<ReviewFilter>("all");
  const [statusMessage, setStatusMessage] = useState<string>("");

  useEffect(() => {
    listCompanies().then((items) => {
      setCompanies(items);
      setLoaded(true);
    });
  }, []);

  const filtered = useMemo(() => {
    let list = [...companies].sort((a, b) => b.score - a.score);
    if (stageFilter !== "all") list = list.filter((c) => c.stage === stageFilter);
    if (reviewFilter !== "all") {
      list = list.filter((c) => (c.review_status ?? "new") === reviewFilter);
    }
    return list;
  }, [companies, stageFilter, reviewFilter]);

  const totals = useMemo(() => {
    const total = companies.length;
    const above80 = companies.filter((c) => c.score >= 80).length;
    const approved = companies.filter((c) => (c.review_status ?? "new") === "approved").length;
    const avg = total ? Math.round(companies.reduce((s, c) => s + c.score, 0) / total) : 0;
    return { total, above80, approved, avg };
  }, [companies]);

  async function onAddDomain() {
    if (!domain.trim()) return;
    setAdding(true);
    setStatusMessage("");
    try {
      const result = await addSeed({ domain: domain.trim(), company_name: name.trim() });
      if (result.added) {
        setStatusMessage(`Added ${result.row.domain} to seed CSV. Run analysis below or via CLI.`);
      } else {
        setStatusMessage(`${result.row.domain} already exists in the seed CSV.`);
      }
      setDomain("");
      setName("");
    } catch {
      setStatusMessage("Failed to add domain. Is the backend running?");
    } finally {
      setAdding(false);
    }
  }

  async function onAnalyzeDomain() {
    if (!domain.trim()) return;
    setAnalyzing(true);
    setStatusMessage("");
    try {
      const profile = await analyzeDomain(domain.trim());
      setCompanies((prev) => [profile, ...prev.filter((p) => p.domain !== profile.domain)]);
      setStatusMessage(`Analyzed ${profile.domain} — score ${profile.score}.`);
      setDomain("");
      setName("");
    } catch {
      setStatusMessage("Analysis failed. Is the backend running?");
    } finally {
      setAnalyzing(false);
    }
  }

  async function onChangeReviewStatus(target: string, status: ReviewStatus) {
    try {
      const updated = await apiSetReviewStatus(target, status);
      setCompanies((prev) => prev.map((c) => (c.domain === target ? updated : c)));
    } catch {
      setStatusMessage(`Failed to update review status for ${target}.`);
    }
  }

  return (
    <main className="mx-auto min-h-screen max-w-7xl px-6 py-8">
      <section className="rounded-3xl bg-slate-950 p-8 text-white shadow-xl">
        <div className="max-w-3xl">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-400">Integration Scout</p>
          <h1 className="mt-4 text-4xl font-bold tracking-tight md:text-5xl">
            Find companies that need integrations built, then turn evidence into outbound.
          </h1>
          <p className="mt-4 text-base leading-7 text-slate-300">
            Add a domain, analyze it, review the suggested persona/email/demo, mark approved, and export to Clay.
          </p>
        </div>
        <div className="mt-6 grid gap-3 md:grid-cols-[1.4fr_1fr_auto_auto]">
          <input
            value={domain}
            onChange={(event) => setDomain(event.target.value)}
            className="rounded-2xl border border-white/10 bg-white/10 px-4 py-3 text-white outline-none placeholder:text-slate-400"
            placeholder="domain.com"
          />
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            className="rounded-2xl border border-white/10 bg-white/10 px-4 py-3 text-white outline-none placeholder:text-slate-400"
            placeholder="Company name (optional)"
          />
          <button
            onClick={onAddDomain}
            disabled={adding || !domain.trim()}
            className="rounded-2xl border border-white/20 bg-white/5 px-5 py-3 font-semibold text-white disabled:opacity-50"
          >
            {adding ? "Adding..." : "Add to seed list"}
          </button>
          <button
            onClick={onAnalyzeDomain}
            disabled={analyzing || !domain.trim()}
            className="rounded-2xl bg-white px-5 py-3 font-semibold text-slate-950 disabled:opacity-50"
          >
            {analyzing ? "Analyzing..." : "Analyze now"}
          </button>
        </div>
        <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-300">
          <div>
            <span className="text-slate-400">"Add to seed list"</span> writes to{" "}
            <code className="rounded bg-white/10 px-1">backend/data/seed_companies.csv</code> for batch analysis.{" "}
            <span className="text-slate-400">"Analyze now"</span> runs immediately and adds the company to your store.
          </div>
          <div className="flex gap-2">
            <a
              href={clayExportUrl()}
              className="rounded-xl border border-white/20 px-4 py-2 font-semibold text-white"
            >
              Export all
            </a>
            <a
              href={clayExportUrl("approved")}
              className="rounded-xl bg-emerald-500 px-4 py-2 font-semibold text-white"
            >
              Export approved ({totals.approved})
            </a>
          </div>
        </div>
        {statusMessage ? (
          <p className="mt-3 rounded-xl bg-white/10 px-4 py-2 text-sm text-white">{statusMessage}</p>
        ) : null}
      </section>

      <section className="mt-6 grid gap-4 md:grid-cols-4">
        <Metric label="Companies" value={totals.total.toString()} />
        <Metric label="Score ≥ 80" value={totals.above80.toString()} />
        <Metric label="Approved" value={totals.approved.toString()} />
        <Metric label="Avg score" value={totals.total ? totals.avg.toString() : "—"} />
      </section>

      <section className="mt-8 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold text-slate-950">Prospect queue</h2>
          <p className="text-sm text-slate-500">
            Review the suggested persona, email, and demo. Approve, reject, or flag for research.
          </p>
        </div>
        <div className="flex gap-2">
          <select
            value={reviewFilter}
            onChange={(event) => setReviewFilter(event.target.value as ReviewFilter)}
            className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm"
          >
            <option value="all">All review statuses</option>
            <option value="new">New</option>
            <option value="approved">Approved</option>
            <option value="needs_research">Needs research</option>
            <option value="skip">Rejected</option>
          </select>
          <select
            value={stageFilter}
            onChange={(event) => setStageFilter(event.target.value)}
            className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm"
          >
            <option value="all">All stages</option>
            <option value="outbound_ready">Outbound ready</option>
            <option value="scored">Scored</option>
            <option value="profiled">Profiled</option>
            <option value="disqualified">Disqualified</option>
          </select>
        </div>
      </section>

      {!loaded ? (
        <section className="mt-5 rounded-2xl border border-slate-200 bg-white p-10 text-center text-sm text-slate-500">
          Loading…
        </section>
      ) : companies.length === 0 ? (
        <EmptyState />
      ) : filtered.length === 0 ? (
        <section className="mt-5 rounded-2xl border border-slate-200 bg-white p-10 text-center text-sm text-slate-500">
          No companies match the current filters.
        </section>
      ) : (
        <section className="mt-5 grid gap-4 lg:grid-cols-2">
          {filtered.map((company) => (
            <CompanyCard
              key={company.id}
              company={company}
              onChangeReviewStatus={onChangeReviewStatus}
            />
          ))}
        </section>
      )}
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="text-sm text-slate-500">{label}</div>
      <div className="mt-2 text-3xl font-bold text-slate-950">{value}</div>
    </div>
  );
}

function EmptyState() {
  return (
    <section className="mt-5 rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
      <h3 className="text-xl font-bold text-slate-950">No companies yet.</h3>
      <p className="mt-2 text-sm text-slate-600">
        Add a domain above to get started, or seed your list from the CLI:
      </p>
      <pre className="mx-auto mt-4 inline-block rounded-xl bg-slate-50 px-4 py-3 text-left text-xs text-slate-700">
{`python scripts/radar.py add-domain monk.ai --name Monk
python scripts/radar.py run`}
      </pre>
      <p className="mt-3 text-xs text-slate-500">
        See <code className="rounded bg-slate-100 px-1">README.md</code> for the full workflow.
      </p>
    </section>
  );
}
