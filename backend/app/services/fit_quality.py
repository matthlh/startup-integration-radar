"""Compute fit_quality + prospect_reasoning for a CompanyProfile.

Separate from `score` (0–100) on purpose. A company can score 85 but still be
a bad outbound target — e.g., a parked domain where signals all came from junk
text, or a mature horizontal platform that already has 1000+ integrations.

fit_quality answers a different question: *should we actually reach out?*
"""

from __future__ import annotations

from app.schemas import CompanyProfile, FitQuality, SignalName
from app.services.destinations import is_mature_platform


def compute_fit_quality(profile: CompanyProfile, *, combined_text: str = "") -> tuple[FitQuality, str]:
    """Return (FitQuality, prospect_reasoning) for the given profile.

    Order matters: bad-domain detection runs first because it overrides any
    score-driven label. Then mature-platform, then score-based banding.
    """
    # 1. Bad domain — parked / unreachable / placeholder.
    warning = (profile.crawl_quality_warning or "").lower()
    if warning:
        bad_signals = (
            "parked",
            "placeholder",
            "no pages were fetched",
            "homepage was not reachable",
            "very little text",
        )
        if any(s in warning for s in bad_signals):
            return (
                FitQuality.bad_fit,
                (
                    "Verify domain manually — the homepage we crawled looks like a parked, "
                    "directory, or unreachable page. Score is unreliable. Confirm the real "
                    "product URL before contacting."
                ),
            )

    # 2. Mature horizontal platform — already has a huge integration ecosystem.
    if is_mature_platform(profile.domain, combined_text):
        reasoning = (
            f"{profile.name} already runs a mature horizontal platform with a public app "
            "marketplace. A 'we'll build integrations for you' pitch is unlikely to land. "
            "Stronger angles: implementation/services for their long-tail customers, or "
            "ecosystem-expansion partnerships."
        )
        return FitQuality.mature_platform, reasoning

    # 3. Score-banded fit, weighted by signal mix.
    positive_signals = {s.signal for s in profile.signal_scores if s.points > 0}
    has_strong_signals = bool(
        positive_signals
        & {
            SignalName.integration_language,
            SignalName.customer_system_complexity,
            SignalName.workflow_product,
        }
    )

    if profile.score >= 75 and has_strong_signals:
        return (
            FitQuality.strong_fit,
            (
                f"{profile.name} shows multiple strong, evidence-grounded integration signals "
                "(named systems, customer-facing workflows). Worth a personalized outreach with "
                "a concrete demo concept tied to the systems mentioned in the evidence."
            ),
        )

    if profile.score >= 50:
        return (
            FitQuality.possible_fit,
            (
                f"{profile.name} has some integration evidence but it's not overwhelming. "
                "Treat as a discovery conversation rather than a direct pitch — confirm the "
                "actual integration pain point with the prospect before assuming a build is needed."
            ),
        )

    if profile.score >= 25:
        return (
            FitQuality.weak_fit,
            (
                f"Few integration signals on {profile.name}'s public surface. Either deprioritize, "
                "or run additional manual research before outreach."
            ),
        )

    return (
        FitQuality.weak_fit,
        (
            f"Very limited public signal for {profile.name}. Not recommended for outbound until "
            "you've manually verified the product surface and customer-system needs."
        ),
    )
