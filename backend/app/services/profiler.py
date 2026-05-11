from __future__ import annotations

import re

from app.core.domain import company_name_from_domain, normalize_domain, website_url
from app.core.scoring import score_evidence
from app.core.signal_rules import get_config
from app.core.signals import extract_evidence, summarize_evidence
from app.providers.web_fetcher import FetchedPage, classify_page_type, fetch_company_pages
from app.schemas import CompanyProfile, Confidence, FitQuality, PipelineStage
from app.services.competitive import find_competitive_triggers
from app.services.fit_quality import compute_fit_quality
from app.services.outreach import choose_likely_systems, make_demo_concept, make_integration_hypothesis, make_outreach
from app.services.persona import recommend_personas_with_reasoning, select_primary_persona


EMPLOYEE_PATTERNS = [
    re.compile(r"(?:team of|team size|company of|we are)\s+(?:about|around|over|more than|under|less than)?\s*(\d{1,5})\s+(?:people|employees|team members)", re.I),
    re.compile(r"(\d{1,5})\s*[-–]\s*(?:person|people|employee)\s+(?:team|company)", re.I),
    re.compile(r"(\d{1,5})\+\s+(?:employees|people|team members)", re.I),
]

# Whole-phrase regexes for the "small/large company" fallback. Substring matches
# fired on words like "founding" inside "since their founding" and tagged
# 350-person unicorns as 25-person founder-led shops.
SMALL_COMPANY_PHRASES = [
    re.compile(r"\bseed stage\b", re.I),
    re.compile(r"\bpre[- ]seed\b", re.I),
    re.compile(r"\bsmall team of\b", re.I),
    re.compile(r"\bfounding team is\b", re.I),
    re.compile(r"\bfounding team of\b", re.I),
    re.compile(r"\bjust\s+\d+\s+(?:of us|people)\b", re.I),
]
LARGE_COMPANY_PHRASES = [
    re.compile(r"\bseries b\b", re.I),
    re.compile(r"\bseries c\b", re.I),
    re.compile(r"\bseries d\b", re.I),
    re.compile(r"\benterprise scale\b", re.I),
    re.compile(r"\bglobal team of\b", re.I),
    re.compile(r"\bglobal company\b", re.I),
    re.compile(r"\bover \d{3,}\s+(?:employees|people)\b", re.I),
]

# Hints that the homepage we fetched is parked, generic, or otherwise not the
# company we intended to crawl. Used to set crawl_quality_warning so the
# operator can see at a glance that the row is unreliable.
PARKED_DOMAIN_PHRASES = [
    "this domain is for sale",
    "buy this domain",
    "domain for sale",
    "godaddy",
    "namecheap",
    "directory of useful information",
    "register this domain",
    "parked",
    "checking your browser",
]


DEFAULT_AI_CATEGORY = "vertical AI / workflow automation"
DEFAULT_FALLBACK_CATEGORY = "B2B workflow software"

# Weight per page-type for category inference. The homepage dominates;
# careers/docs/integrations mention customer systems (Procore, Autodesk, NetSuite)
# that should count as integration evidence but not redirect the company's category.
PAGE_TYPE_WEIGHTS: dict[str, float] = {
    "homepage": 1.0,
    "other": 0.5,
    "blog": 0.3,
    "integrations": 0.15,
    "docs": 0.10,
    "careers": 0.10,
}

# Multipliers within the homepage — title/meta carry more weight than body text.
HOMEPAGE_FIELD_WEIGHTS: dict[str, float] = {
    "title": 4.0,
    "meta_description": 4.0,
    "og_description": 3.0,
    "h1_h2": 3.0,
    "body": 2.0,
}


def _count_hits(text: str, keyword: str) -> int:
    if not text or not keyword:
        return 0
    return text.lower().count(keyword.lower())


def _homepage_field_texts(homepage: FetchedPage) -> dict[str, str]:
    return {
        "title": homepage.title,
        "meta_description": homepage.meta_description,
        "og_description": homepage.og_description,
        "h1_h2": " ".join(homepage.h1 + homepage.h2),
        "body": homepage.text,
    }


def _category_confidence(top_score: float, runner_up: float) -> str:
    if top_score >= 6 and (runner_up == 0 or top_score >= runner_up * 2):
        return "high"
    if top_score >= 3:
        return "medium"
    return "low"


def infer_category_weighted(
    homepage: FetchedPage | None,
    secondary_pages: list[FetchedPage],
) -> tuple[str, str, list[str]]:
    """Infer the company's vertical with page-type-weighted evidence.

    Returns (inferred_category, category_confidence, category_evidence).
    Homepage signals (title, meta description, headings, body) drive the result;
    careers/docs/integrations pages contribute very little so an integrations
    company with Procore/Autodesk in job postings does not get tagged as
    construction tech.
    """
    categories = get_config().get("categories", []) or []
    if not categories:
        return DEFAULT_FALLBACK_CATEGORY, "low", []

    scores: dict[str, float] = {entry["name"]: 0.0 for entry in categories}
    evidence: dict[str, list[str]] = {entry["name"]: [] for entry in categories}

    if homepage is not None:
        fields = _homepage_field_texts(homepage)
        for entry in categories:
            cat = entry["name"]
            for kw in entry.get("keywords", []):
                for field_name, field_text in fields.items():
                    hits = _count_hits(field_text, kw)
                    if not hits:
                        continue
                    weight = HOMEPAGE_FIELD_WEIGHTS[field_name] * PAGE_TYPE_WEIGHTS["homepage"]
                    scores[cat] += hits * weight
                    evidence[cat].append(f"matched '{kw}' in homepage {field_name.replace('_', ' ')}")

    for page in secondary_pages:
        weight = PAGE_TYPE_WEIGHTS.get(page.page_type, PAGE_TYPE_WEIGHTS["other"])
        if weight <= 0:
            continue
        for entry in categories:
            cat = entry["name"]
            for kw in entry.get("keywords", []):
                hits = _count_hits(page.text, kw)
                if not hits:
                    continue
                scores[cat] += hits * weight
                evidence[cat].append(f"matched '{kw}' on {page.page_type} page")

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    top_name, top_score = ranked[0]
    runner_up_score = ranked[1][1] if len(ranked) > 1 else 0.0

    if top_score < 1.0:
        # Nothing strong matched — try the AI/automation fallback against the homepage.
        homepage_text = (homepage.text if homepage else "").lower()
        if "ai" in homepage_text or "automation" in homepage_text:
            return DEFAULT_AI_CATEGORY, "low", []
        return DEFAULT_FALLBACK_CATEGORY, "low", []

    confidence = _category_confidence(top_score, runner_up_score)
    # Cap evidence list length so it stays Clay-friendly.
    return top_name, confidence, evidence[top_name][:6]


def infer_category(text: str) -> str:
    """Legacy single-string entry point — kept so existing callers keep working.

    Prefer infer_category_weighted() with full FetchedPage objects.
    """
    lowered = text.lower()
    for entry in get_config().get("categories", []):
        if any(kw in lowered for kw in entry.get("keywords", [])):
            return entry["name"]
    if "ai" in lowered or "automation" in lowered:
        return DEFAULT_AI_CATEGORY
    return DEFAULT_FALLBACK_CATEGORY


SUMMARY_MIN_LEN = 40
SUMMARY_MAX_LEN = 280


def _clean_summary(value: str) -> str:
    """Collapse whitespace and trim trailing punctuation noise."""
    return " ".join(value.split()).strip()


def select_company_summary(homepage: FetchedPage | None) -> tuple[str, str]:
    """Pick the best deterministic company summary and return (summary, source).

    Priority:
      1. <meta name="description">
      2. <meta property="og:description">
      3. homepage H1/H2 (first H1, optionally joined with first H2)
      4. fallback: first ~280 chars of cleaned page text
    Returns ("", "") if the homepage is missing.
    """
    if homepage is None:
        return "", ""

    meta = _clean_summary(homepage.meta_description)
    if SUMMARY_MIN_LEN <= len(meta) <= SUMMARY_MAX_LEN * 2:
        return meta[:SUMMARY_MAX_LEN].rstrip(), "meta_description"

    og = _clean_summary(homepage.og_description)
    if SUMMARY_MIN_LEN <= len(og) <= SUMMARY_MAX_LEN * 2:
        return og[:SUMMARY_MAX_LEN].rstrip(), "og_description"

    # Try to build a summary from H1 and H2.
    h1 = _clean_summary(homepage.h1[0]) if homepage.h1 else ""
    h2 = _clean_summary(homepage.h2[0]) if homepage.h2 else ""
    if h1 and h2 and h1.lower() != h2.lower():
        combined = f"{h1} — {h2}"
    else:
        combined = h1 or h2
    if len(combined) >= SUMMARY_MIN_LEN:
        return combined[:SUMMARY_MAX_LEN].rstrip(), "h1_h2"

    cleaned = _clean_summary(homepage.text)
    if len(cleaned) >= SUMMARY_MIN_LEN:
        return cleaned[:SUMMARY_MAX_LEN].rstrip(), "cleaned_text"

    return "", ""


def infer_one_liner(name: str, company_summary: str, fallback_text: str) -> str:
    summary = _clean_summary(company_summary)
    if summary:
        return f"I was reading about {name} — {summary}"
    clean = " ".join(fallback_text.split())
    if len(clean) < 80:
        return f"I was looking at {name}'s product and the workflow it supports."
    return f"I was looking at {name} and noticed you help teams with {clean[:180].rstrip()}..."


def infer_employee_count_estimate(text: str) -> int | None:
    clean = " ".join(text.split())
    candidates: list[int] = []
    for pattern in EMPLOYEE_PATTERNS:
        for match in pattern.finditer(clean):
            try:
                value = int(match.group(1))
            except (TypeError, ValueError):
                continue
            if 1 <= value <= 10000:
                candidates.append(value)
    if candidates:
        return max(candidates)

    if any(pattern.search(clean) for pattern in SMALL_COMPANY_PHRASES):
        return 25
    if any(pattern.search(clean) for pattern in LARGE_COMPANY_PHRASES):
        return 100
    return None


def detect_crawl_quality_warning(
    homepage: FetchedPage | None, pages: list[FetchedPage]
) -> str:
    """Return a human-readable warning string when the crawl looks unreliable.

    Empty string means no warning. Surfaces in the dashboard and CSV so junk
    rows (parked domains, blocked crawlers, missing homepages) are not silently
    shipped to Clay.
    """
    if not pages:
        return "No pages were fetched — domain may be unreachable or blocking the crawler."
    if homepage is None:
        return "Homepage was not reachable; analysis ran against secondary pages only."

    title = (homepage.title or "").lower()
    body = (homepage.text or "").lower()
    haystack = f"{title} {homepage.meta_description.lower()} {body[:2000]}"
    for phrase in PARKED_DOMAIN_PHRASES:
        if phrase in haystack:
            return f"Homepage looks like a parked or placeholder page (matched '{phrase}')."

    if len(homepage.text) < 500:
        return "Homepage returned very little text — analysis may be unreliable."
    if len(pages) < 2:
        return "Only the homepage was reachable; secondary pages (docs, careers, etc.) failed."
    return ""


async def profile_company(domain: str, use_llm: bool = False) -> CompanyProfile:
    normalized = normalize_domain(domain)
    pages = await fetch_company_pages(normalized)
    combined_text = "\n\n".join(page.text for page in pages)
    source_url = pages[0].url if pages else website_url(normalized)
    page_title = pages[0].title if pages else ""

    evidence = []
    for page in pages:
        evidence.extend(extract_evidence(page.text, source_url=page.url, page_title=page.title))
    if not evidence and combined_text:
        evidence = extract_evidence(combined_text, source_url=source_url, page_title=page_title)

    score, confidence, signal_scores, stage, disqualification_reason = score_evidence(evidence)
    name = company_name_from_domain(normalized)
    # Page-type weighted inference: homepage signals dominate so docs/careers
    # mentions of customer systems (Procore, Autodesk, NetSuite) do not redirect
    # the company's vertical.
    for page in pages:
        if not page.page_type or page.page_type == "other":
            page.page_type = classify_page_type(page.url)
    homepage = next((p for p in pages if p.page_type == "homepage"), pages[0] if pages else None)
    secondary_pages = [p for p in pages if p is not homepage]
    inferred_category, category_confidence_str, category_evidence = infer_category_weighted(homepage, secondary_pages)
    systems = choose_likely_systems(
        combined_text,
        # seed_category is unknown here — analyze-csv applies it later and
        # then calls refresh_derived_fields() which recomputes systems.
        inferred_category=inferred_category,
    )
    employee_count_estimate = infer_employee_count_estimate(combined_text)
    company_summary, company_summary_source = select_company_summary(homepage)

    crawl_quality_warning = detect_crawl_quality_warning(homepage, pages)

    # Bad-domain detection: a parked / placeholder / unreachable homepage caps
    # the score at 20 so a junk page can't accidentally show up as a hot lead.
    bad_domain_signals = ("parked", "placeholder", "no pages were fetched", "homepage was not reachable")
    if crawl_quality_warning and any(s in crawl_quality_warning.lower() for s in bad_domain_signals):
        score = min(score, 20)
        stage = PipelineStage.profiled

    profile = CompanyProfile(
        name=name,
        domain=normalized,
        website_url=website_url(normalized),
        one_liner=infer_one_liner(name, company_summary, combined_text),
        company_summary=company_summary,
        company_summary_source=company_summary_source,
        category=inferred_category,
        inferred_category=inferred_category,
        category_confidence=Confidence(category_confidence_str),
        category_evidence=category_evidence,
        customer_type="B2B teams using existing operational software",
        employee_count_estimate=employee_count_estimate,
        likely_customer_systems=systems,
        pages_fetched=[page.url for page in pages],
        crawl_quality_warning=crawl_quality_warning,
        evidence=evidence,
        evidence_summary=summarize_evidence(evidence),
        competitive_triggers=find_competitive_triggers(evidence),
        signal_scores=signal_scores,
        score=score,
        confidence=confidence,
        stage=stage,
        disqualification_reason=disqualification_reason,
    )
    profile.integration_need_hypothesis = make_integration_hypothesis(profile)
    profile.primary_persona = select_primary_persona(employee_count_estimate)
    personas, persona_reasoning = recommend_personas_with_reasoning(
        signal_scores, score, employee_count_estimate
    )
    profile.personas = personas
    profile.persona_reasoning = persona_reasoning

    fit_quality, prospect_reasoning = compute_fit_quality(profile, combined_text=combined_text)
    profile.fit_quality = fit_quality
    profile.prospect_reasoning = prospect_reasoning

    # Don't bother generating outreach/demo for bad-fit rows — they go straight
    # to the operator for manual verification.
    if score >= 55 and stage != PipelineStage.disqualified and fit_quality != FitQuality.bad_fit:
        profile.outreach = make_outreach(profile)
        profile.demo = await make_demo_concept(profile, use_llm=use_llm)
        profile.stage = PipelineStage.outbound_ready
    return profile


async def refresh_derived_fields(profile: CompanyProfile, use_llm: bool = False) -> CompanyProfile:
    """Re-derive hypothesis / outreach / demo after the caller mutates the profile.

    Use after applying seed-CSV overrides (e.g. profile.category = seed.category)
    so the integration hypothesis, outreach, demo concept, and destination
    systems reflect the final category instead of the inferred one.
    """
    # Re-pick destination systems with the new (seed-overridden) category.
    # We don't have the original combined_text anymore, but evidence_summary +
    # company_summary contain the brand names we extracted on the first pass,
    # so the evidence-first picker still surfaces them.
    haystack = " ".join(
        filter(
            None,
            [
                profile.evidence_summary,
                profile.company_summary,
                profile.one_liner,
            ],
        )
    )
    profile.likely_customer_systems = choose_likely_systems(
        haystack,
        seed_category=profile.category or "",
        inferred_category=profile.inferred_category or profile.category or "",
    )

    profile.integration_need_hypothesis = make_integration_hypothesis(profile)

    fit_quality, prospect_reasoning = compute_fit_quality(profile, combined_text=haystack)
    profile.fit_quality = fit_quality
    profile.prospect_reasoning = prospect_reasoning

    if (
        profile.score >= 55
        and profile.stage != PipelineStage.disqualified
        and fit_quality != FitQuality.bad_fit
    ):
        profile.outreach = make_outreach(profile)
        profile.demo = await make_demo_concept(profile, use_llm=use_llm)
    return profile
