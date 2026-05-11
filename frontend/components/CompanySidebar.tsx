"use client";

import { useMemo, useState } from "react";
import type { CompanyProfile, ReviewStatus } from "../lib/types";

type QuickFilter = "all" | "hot" | "approved" | "needs_research" | "new";

export function cardIdForDomain(domain: string): string {
  // Stable, anchor-friendly id for scrollIntoView lookups.
  return `company-${domain.replace(/[^a-z0-9-]/gi, "-")}`;
}

const QUICK_FILTERS: { value: QuickFilter; label: string; tone: string }[] = [
  { value: "all", label: "All", tone: "bg-slate-100 text-slate-700" },
  { value: "hot", label: "Hot", tone: "bg-rose-100 text-rose-700" },
  { value: "approved", label: "Approved", tone: "bg-emerald-100 text-emerald-800" },
  { value: "needs_research", label: "Needs research", tone: "bg-amber-100 text-amber-800" },
  { value: "new", label: "New", tone: "bg-slate-100 text-slate-600" },
];

interface CompanySidebarProps {
  companies: CompanyProfile[];
  activeDomain: string | null;
  onSelect: (domain: string) => void;
  expanded: boolean;
  onToggleExpanded: () => void;
  /** Mobile drawer is rendered separately; on mobile we hide the toggle button. */
  hideToggleOnMobile?: boolean;
  /** When true, the sidebar drops its own rounding/shadow because its container is the chrome. */
  edgeMode?: boolean;
}

function passesQuickFilter(company: CompanyProfile, filter: QuickFilter): boolean {
  const status = (company.review_status ?? "new") as ReviewStatus;
  switch (filter) {
    case "all":
      return true;
    case "hot":
      return company.score >= 80;
    case "approved":
      return status === "approved";
    case "needs_research":
      return status === "needs_research";
    case "new":
      return status === "new";
    default:
      return true;
  }
}

export function CompanySidebar({
  companies,
  activeDomain,
  onSelect,
  expanded,
  onToggleExpanded,
  hideToggleOnMobile = false,
  edgeMode = false,
}: CompanySidebarProps) {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<QuickFilter>("all");

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    return [...companies]
      .sort((a, b) => b.score - a.score)
      .filter((c) => passesQuickFilter(c, filter))
      .filter((c) => {
        if (!term) return true;
        return c.name.toLowerCase().includes(term) || c.domain.toLowerCase().includes(term);
      });
  }, [companies, search, filter]);

  const chrome = edgeMode
    ? "h-full w-full"
    : "sticky top-6 max-h-[calc(100vh-3rem)] rounded-2xl border border-slate-200 shadow-sm";
  const railChrome = edgeMode
    ? "h-full w-full"
    : "sticky top-6 h-[calc(100vh-3rem)] w-12 rounded-2xl border border-slate-200 shadow-sm";

  // Collapsed rail: just an expand button + a count badge.
  if (!expanded) {
    return (
      <aside
        className={`flex flex-col items-center bg-white py-3 ${railChrome}`}
      >
        <button
          type="button"
          onClick={onToggleExpanded}
          className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900"
          aria-label="Expand companies sidebar"
          title="Expand companies"
        >
          <ChevronRightIcon />
        </button>
        <div className="mt-3 rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">
          {companies.length}
        </div>
      </aside>
    );
  }

  return (
    <aside className={`flex flex-col overflow-hidden bg-white ${chrome}`}>
      <header className="flex items-center justify-between gap-2 border-b border-slate-100 px-4 py-3">
        <div>
          <h3 className="text-sm font-bold text-slate-950">Companies</h3>
          <p className="text-xs text-slate-500">{companies.length} in your queue</p>
        </div>
        <button
          type="button"
          onClick={onToggleExpanded}
          className={`rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900 ${
            hideToggleOnMobile ? "hidden lg:inline-flex" : ""
          }`}
          aria-label="Collapse companies sidebar"
          title="Collapse"
        >
          <ChevronLeftIcon />
        </button>
      </header>

      <div className="border-b border-slate-100 px-4 py-3">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by name or domain…"
          className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm outline-none focus:border-slate-400 focus:bg-white"
        />
        <div className="mt-3 flex flex-wrap gap-1.5">
          {QUICK_FILTERS.map((option) => {
            const active = filter === option.value;
            return (
              <button
                key={option.value}
                type="button"
                onClick={() => setFilter(option.value)}
                className={`rounded-full px-2.5 py-1 text-xs font-semibold transition-colors ${
                  active
                    ? "bg-slate-900 text-white"
                    : `${option.tone} hover:opacity-80`
                }`}
              >
                {option.label}
              </button>
            );
          })}
        </div>
      </div>

      <ol className="flex-1 overflow-y-auto px-2 py-2">
        {filtered.length === 0 ? (
          <li className="px-3 py-4 text-center text-xs text-slate-500">
            No companies match. Try clearing the search or filter.
          </li>
        ) : (
          filtered.map((company) => (
            <SidebarRow
              key={company.id}
              company={company}
              active={activeDomain === company.domain}
              onSelect={() => onSelect(company.domain)}
            />
          ))
        )}
      </ol>
    </aside>
  );
}

function SidebarRow({
  company,
  active,
  onSelect,
}: {
  company: CompanyProfile;
  active: boolean;
  onSelect: () => void;
}) {
  const status: ReviewStatus = (company.review_status ?? "new") as ReviewStatus;
  return (
    <li>
      <button
        type="button"
        onClick={onSelect}
        className={`group flex w-full items-start gap-2 rounded-lg px-2.5 py-2 text-left transition-colors ${
          active ? "bg-slate-900 text-white" : "hover:bg-slate-50"
        }`}
      >
        <ScoreBadge score={company.score} dark={active} />
        <div className="min-w-0 flex-1">
          <div className={`truncate text-sm font-semibold ${active ? "text-white" : "text-slate-900"}`}>
            {company.name}
          </div>
          <div className={`truncate text-xs ${active ? "text-slate-300" : "text-slate-500"}`}>
            {company.domain}
          </div>
        </div>
        <ReviewDot status={status} active={active} />
      </button>
    </li>
  );
}

function ScoreBadge({ score, dark = false }: { score: number; dark?: boolean }) {
  let tone = "bg-slate-200 text-slate-700";
  if (score >= 80) tone = "bg-rose-500 text-white";
  else if (score >= 60) tone = "bg-amber-400 text-amber-950";
  else if (score >= 30) tone = "bg-slate-300 text-slate-800";
  if (dark) {
    // Keep some contrast inside the dark active row.
    tone =
      score >= 80 ? "bg-rose-400 text-white"
      : score >= 60 ? "bg-amber-300 text-amber-950"
      : "bg-slate-600 text-white";
  }
  return (
    <span className={`mt-0.5 inline-flex h-7 w-9 shrink-0 items-center justify-center rounded-md text-xs font-bold ${tone}`}>
      {score}
    </span>
  );
}

function ReviewDot({ status, active }: { status: ReviewStatus; active: boolean }) {
  const map: Record<ReviewStatus, string> = {
    approved: "bg-emerald-500",
    needs_research: "bg-amber-500",
    skip: "bg-rose-500",
    new: active ? "bg-slate-400" : "bg-slate-300",
  };
  const label: Record<ReviewStatus, string> = {
    approved: "Approved",
    needs_research: "Needs research",
    skip: "Rejected",
    new: "New",
  };
  return (
    <span
      className={`mt-1.5 inline-block h-2 w-2 shrink-0 rounded-full ${map[status]}`}
      title={label[status]}
      aria-label={`Review status: ${label[status]}`}
    />
  );
}

function ChevronLeftIcon() {
  return (
    <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
      <path
        fillRule="evenodd"
        d="M12.78 5.22a.75.75 0 010 1.06L9.06 10l3.72 3.72a.75.75 0 11-1.06 1.06l-4.25-4.25a.75.75 0 010-1.06l4.25-4.25a.75.75 0 011.06 0z"
        clipRule="evenodd"
      />
    </svg>
  );
}

function ChevronRightIcon() {
  return (
    <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
      <path
        fillRule="evenodd"
        d="M7.22 14.78a.75.75 0 010-1.06L10.94 10 7.22 6.28a.75.75 0 011.06-1.06l4.25 4.25a.75.75 0 010 1.06l-4.25 4.25a.75.75 0 01-1.06 0z"
        clipRule="evenodd"
      />
    </svg>
  );
}
