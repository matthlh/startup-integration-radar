from __future__ import annotations

import re
from collections import defaultdict

from app.core.signal_rules import KEYWORD_EVIDENCE_TYPE, SIGNAL_KEYWORDS, SIGNAL_WEIGHTS
from app.schemas import Evidence, EvidenceType, SignalName


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def snippet_around(text: str, keyword: str, window: int = 120) -> str:
    lowered = text.lower()
    idx = lowered.find(keyword.lower())
    if idx < 0:
        return keyword
    start = max(0, idx - window)
    end = min(len(text), idx + len(keyword) + window)
    return normalize_text(text[start:end])


def keyword_present(text: str, keyword: str) -> bool:
    """Return True only for meaningful keyword matches.

    This avoids treating common verbs like "merge" as competitor evidence while
    still catching branded strings such as Merge.dev, Merge API, and Paragon.
    """
    lowered = text.lower()
    kw = keyword.lower()
    if kw == "paragon":
        return bool(re.search(r"\bparagon\b", lowered))
    if kw.startswith("merge") and kw not in {"merge.dev", "merge api", "merge unified api"}:
        return False
    if len(kw) <= 4:
        return bool(re.search(rf"\b{re.escape(kw)}\b", lowered))
    return kw in lowered


def infer_source_context(source_url: str = "", page_title: str = "", snippet: str = "") -> str:
    haystack = f"{source_url} {page_title} {snippet}".lower()
    if any(token in haystack for token in ["careers", "jobs", "greenhouse", "lever", "ashby", "workable"]):
        if any(role in haystack for role in ["backend", "engineer", "engineering", "developer"]):
            return "engineering job posting"
        return "careers page"
    if any(token in haystack for token in ["integrations", "marketplace", "partners"]):
        return "integrations/partners page"
    if any(token in haystack for token in ["docs", "developer", "api", "webhook"]):
        return "developer documentation"
    if any(token in haystack for token in ["security", "soc 2", "compliance"]):
        return "security/enterprise page"
    return "website"


def extract_evidence(text: str, source_url: str = "", page_title: str = "") -> list[Evidence]:
    normalized = normalize_text(text)
    evidence: list[Evidence] = []
    seen: set[tuple[str, str]] = set()

    for signal, keywords in SIGNAL_KEYWORDS.items():
        for keyword in keywords:
            if not keyword_present(normalized, keyword):
                continue
            snippet = snippet_around(normalized, keyword)
            key = (signal.value, keyword.lower(), snippet.lower()[:160])
            if key in seen:
                continue
            seen.add(key)
            evidence_type = KEYWORD_EVIDENCE_TYPE.get(signal, EvidenceType.website_copy)
            source_context = infer_source_context(source_url, page_title, snippet)
            if source_context in {"careers page", "engineering job posting"}:
                evidence_type = EvidenceType.careers
            evidence.append(
                Evidence(
                    type=evidence_type,
                    source_url=source_url,
                    page_title=page_title,
                    snippet=snippet,
                    signal=signal,
                    weight=SIGNAL_WEIGHTS[signal],
                    matched_keyword=keyword,
                    source_context=source_context,
                )
            )
    return evidence[:100]


BUSINESS_SYSTEM_KEYWORDS = {
    "salesforce", "hubspot", "netsuite", "quickbooks", "workday", "snowflake",
    "jira", "procore", "autodesk", "stripe", "sap", "erp", "crm",
}


def _keyword_priority(ev: Evidence) -> int:
    keyword = ev.matched_keyword.lower().strip()
    if keyword in BUSINESS_SYSTEM_KEYWORDS:
        return 5
    if ev.signal == SignalName.competitor_presence:
        return 4
    if ev.signal == SignalName.customer_system_complexity:
        return 3
    if ev.signal == SignalName.integration_language:
        return 2
    if ev.signal == SignalName.developer_surface:
        return 1
    return 0


def summarize_evidence(evidence: list[Evidence], limit: int = 5) -> str:
    """Produce a human-readable proof summary for the GTM operator.

    Example style:
    "Mentioned 'NetSuite' and 'QuickBooks' on an engineering job posting; mentioned
    'webhooks' in developer documentation."
    """
    if not evidence:
        return "No strong public integration evidence found yet. Add manual notes or run deeper discovery."

    priority = sorted(
        evidence,
        key=lambda ev: (
            ev.signal == SignalName.competitor_presence,
            ev.type == EvidenceType.careers,
            _keyword_priority(ev),
            ev.weight,
            ev.source_context != "website",
        ),
        reverse=True,
    )

    grouped: dict[str, list[Evidence]] = defaultdict(list)
    for ev in priority:
        if ev.matched_keyword:
            grouped[ev.source_context or "website"].append(ev)
        if len(grouped) >= limit and sum(len(v) for v in grouped.values()) >= limit:
            break

    clauses: list[str] = []
    for source_context, items in list(grouped.items())[:limit]:
        unique_keywords: list[str] = []
        for item in sorted(items, key=_keyword_priority, reverse=True):
            keyword = item.matched_keyword.strip()
            if keyword and keyword.lower() not in {k.lower() for k in unique_keywords}:
                unique_keywords.append(keyword)
            if len(unique_keywords) >= 3:
                break
        if not unique_keywords:
            continue
        keyword_text = _join_quoted(unique_keywords)
        clauses.append(f"Mentioned {keyword_text} on their {source_context}")

    if clauses:
        return "; ".join(clauses[:limit]) + "."

    top = priority[:limit]
    return " | ".join(ev.snippet[:180] for ev in top)


def _join_quoted(values: list[str]) -> str:
    quoted = [f"'{value}'" for value in values]
    if len(quoted) == 1:
        return quoted[0]
    if len(quoted) == 2:
        return f"{quoted[0]} and {quoted[1]}"
    return f"{', '.join(quoted[:-1])}, and {quoted[-1]}"
