from __future__ import annotations

from collections import defaultdict

from app.core.signal_rules import SIGNAL_MAX_POINTS
from app.schemas import Confidence, Evidence, PipelineStage, SignalName, SignalScore

STRONG_SIGNALS = {
    SignalName.developer_surface,
    SignalName.integration_language,
    SignalName.customer_system_complexity,
    SignalName.workflow_product,
}

# Careers / job postings are routinely keyword-rich (a job ad mentions every
# system the company has ever touched, regardless of whether the product
# actually integrates with it). Halve their weight in the saturation math so
# the product-surface signals dominate. Everything else stays full weight.
HALF_WEIGHT_SOURCES = {"engineering job posting", "careers page"}


def _hit_weight(source_context: str) -> float:
    if source_context in HALF_WEIGHT_SOURCES:
        return 0.5
    return 1.0


def score_evidence(evidence: list[Evidence]) -> tuple[int, Confidence, list[SignalScore], PipelineStage, str]:
    grouped: dict[SignalName, list[Evidence]] = defaultdict(list)
    for ev in evidence:
        if ev.signal:
            grouped[ev.signal].append(ev)

    signal_scores: list[SignalScore] = []
    total = 0
    disqualification_reason = ""

    for signal, max_points in SIGNAL_MAX_POINTS.items():
        hits = grouped.get(signal, [])
        if not hits:
            continue

        if signal == SignalName.disqualifier:
            disqualification_reason = hits[0].snippet
            signal_scores.append(
                SignalScore(
                    signal=signal,
                    points=-35,
                    max_points=max_points,
                    evidence_ids=[hit.id for hit in hits[:3]],
                    reason="Potentially not a B2B integration-heavy company.",
                )
            )
            total -= 35
            continue

        # Saturating score: one hit is a clue, three independent hits are strong
        # evidence. Source-aware: careers-page mentions count half because that
        # page lists every system the company has ever touched, regardless of
        # whether the product actually integrates with it.
        weighted_hit_count = sum(_hit_weight(hit.source_context) for hit in hits)
        base = min(max_points, round((weighted_hit_count / 3) * max_points))
        # Reward higher-signal categories slightly when evidence appears repeatedly.
        weighted_bonus = min(3, sum(max(hit.weight, 0) for hit in hits) // 8)
        points = min(max_points, base + weighted_bonus)
        total += points
        signal_scores.append(
            SignalScore(
                signal=signal,
                points=points,
                max_points=max_points,
                evidence_ids=[hit.id for hit in hits[:5]],
                reason=f"Found {len(hits)} public signal(s) for {signal.value.replace('_', ' ')}.",
            )
        )

    score = max(0, min(100, total))
    confidence = compute_confidence(score, signal_scores)
    stage = PipelineStage.scored if score >= 45 else PipelineStage.profiled
    if disqualification_reason and score < 60:
        stage = PipelineStage.disqualified
    return score, confidence, signal_scores, stage, disqualification_reason


def compute_confidence(score: int, signal_scores: list[SignalScore]) -> Confidence:
    signals = {item.signal for item in signal_scores if item.points > 0}
    strong_signal_count = len(signals & STRONG_SIGNALS)
    if score >= 75 and strong_signal_count >= 3:
        return Confidence.high
    if score >= 55 and strong_signal_count >= 2:
        return Confidence.medium
    return Confidence.low
