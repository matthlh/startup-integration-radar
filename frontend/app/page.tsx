"use client";

import { useEffect, useMemo, useState } from "react";
import { analyzeDomain, clayExportUrl, listCompanies } from "../lib/api";
import type { CompanyProfile } from "../lib/types";
import { CompanyCard } from "../components/CompanyCard";
import { mockCompanies } from "../components/mockData";

export default function Home() {
  const [companies, setCompanies] = useState<CompanyProfile[]>(mockCompanies);
  const [domain, setDomain] = useState("monk.ai");
  const [loading, setLoading] = useState(false);
  const [stageFilter, setStageFilter] = useState("all");

  useEffect(() => {
    listCompanies().then((items) => {
      if (items.length > 0) setCompanies(items);
    });
  }, []);

  const filtered = useMemo(() => {
    const sorted = [...companies].sort((a, b) => b.score - a.score);
    if (stageFilter === "all") return sorted;
    return sorted.filter((company) => company.stage === stageFilter);
  }, [companies, stageFilter]);

  async function onAnalyze() {
    setLoading(true);
    try {
      const result = await analyzeDomain(domain);
      setCompanies((prev) => [result, ...prev.filter((item) => item.domain !== result.domain)]);
    } finally {
      setLoading(false);
    }
  }

  const averageScore = Math.round(companies.reduce((sum, item) => sum + item.score, 0) / companies.length);
  const outboundReady = companies.filter((item) => item.stage === "outbound_ready").length;

  return (
    <main className="mx-auto min-h-screen max-w-7xl px-6 py-8">
      <section className="rounded-3xl bg-slate-950 p-8 text-white shadow-xl">
        <div className="max-w-3xl">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-400">Rutter Integration Radar</p>
          <h1 className="mt-4 text-4xl font-bold tracking-tight md:text-5xl">
            Find companies with integration pain, then turn evidence into outbound.
          </h1>
          <p className="mt-4 text-base leading-7 text-slate-300">
            This dashboard is built for the Monk-style GTM motion: discover companies, collect public evidence,
            score integration need, choose personas, export to Clay, and build demo angles for the strongest prospects.
          </p>
        </div>
        <div className="mt-6 grid gap-3 md:grid-cols-[1fr_auto_auto]">
          <input
            value={domain}
            onChange={(event) => setDomain(event.target.value)}
            className="rounded-2xl border border-white/10 bg-white/10 px-4 py-3 text-white outline-none placeholder:text-slate-400"
            placeholder="monk.ai"
          />
          <button
            onClick={onAnalyze}
            disabled={loading}
            className="rounded-2xl bg-white px-5 py-3 font-semibold text-slate-950 disabled:opacity-60"
          >
            {loading ? "Analyzing..." : "Analyze domain"}
          </button>
          <a href={clayExportUrl()} className="rounded-2xl border border-white/20 px-5 py-3 text-center font-semibold text-white">
            Export Clay CSV
          </a>
        </div>
      </section>

      <section className="mt-6 grid gap-4 md:grid-cols-4">
        <Metric label="Companies" value={companies.length.toString()} />
        <Metric label="Outbound ready" value={outboundReady.toString()} />
        <Metric label="Avg score" value={averageScore.toString()} />
        <Metric label="Top score" value={Math.max(...companies.map((item) => item.score)).toString()} />
      </section>

      <section className="mt-8 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold text-slate-950">Prospect queue</h2>
          <p className="text-sm text-slate-500">Review score, evidence, persona, and demo concept before exporting.</p>
        </div>
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
      </section>

      <section className="mt-5 grid gap-4 lg:grid-cols-2">
        {filtered.map((company) => (
          <CompanyCard key={company.id} company={company} />
        ))}
      </section>
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
