from __future__ import annotations

from typing import Any

from app.core.signal_rules import get_config
from app.schemas import PersonaName, PersonaRecommendation, SignalName, SignalScore


# ─── Config helpers ──────────────────────────────────────────────────────────


def _personas_config() -> dict[str, Any]:
    return get_config().get("personas", {}) or {}


def _persona_rules() -> dict[str, list[dict[str, Any]]]:
    return get_config().get("persona_rules", {}) or {}


def _threshold() -> int:
    return int(_personas_config().get("small_company_threshold", 50))


def _build_persona(key: str) -> PersonaRecommendation:
    cfg = _personas_config().get(key, {}) or {}
    return PersonaRecommendation(
        persona=PersonaName(key),
        titles=cfg.get("titles", [key.title()]),
        why=cfg.get("why", ""),
        priority=cfg.get("priority", 3),
    )


# ─── Condition evaluation ────────────────────────────────────────────────────


def _evaluate_condition(
    condition: dict[str, Any],
    *,
    employee_count_estimate: int | None,
    score: int,
    positive_signals: set[SignalName],
) -> bool:
    """Evaluate one condition block from persona_rules.

    Supported keys:
      employee_count: "unknown" | {"lt": int} | {"gte": int} | {"lte": int} | {"gt": int}
      any_signal: [signal_name, ...]
      score_lt: int
      score_gte: int
    """
    if not condition:
        return True

    if "employee_count" in condition:
        spec = condition["employee_count"]
        if spec == "unknown":
            if employee_count_estimate is not None:
                return False
        elif isinstance(spec, dict):
            if employee_count_estimate is None:
                return False
            for op, value in spec.items():
                value = int(value)
                if op == "lt" and not (employee_count_estimate < value):
                    return False
                if op == "lte" and not (employee_count_estimate <= value):
                    return False
                if op == "gt" and not (employee_count_estimate > value):
                    return False
                if op == "gte" and not (employee_count_estimate >= value):
                    return False
        else:
            return False

    if "any_signal" in condition:
        wanted = {SignalName(s) for s in condition["any_signal"]}
        if not (wanted & positive_signals):
            return False

    if "score_lt" in condition and not (score < int(condition["score_lt"])):
        return False
    if "score_gte" in condition and not (score >= int(condition["score_gte"])):
        return False

    return True


# ─── Public API ──────────────────────────────────────────────────────────────


def select_primary_persona(employee_count_estimate: int | None) -> PersonaRecommendation:
    """Return the primary persona purely from headcount.

    Mirrors the YAML primary rules but kept as a thin helper so existing callers
    that only care about the headcount-driven primary stay simple.
    """
    if employee_count_estimate is None:
        return _build_persona("product")
    if employee_count_estimate < _threshold():
        return _build_persona("founder")
    return _build_persona("product")


def recommend_personas(
    signal_scores: list[SignalScore],
    score: int,
    employee_count_estimate: int | None = None,
) -> list[PersonaRecommendation]:
    """Apply persona_rules from signals.yaml and return ranked persona list.

    Use `recommend_personas_with_reasoning` if you want the per-rule reason
    strings as well.
    """
    personas, _reasoning = recommend_personas_with_reasoning(
        signal_scores, score, employee_count_estimate
    )
    return personas


def recommend_personas_with_reasoning(
    signal_scores: list[SignalScore],
    score: int,
    employee_count_estimate: int | None = None,
) -> tuple[list[PersonaRecommendation], list[str]]:
    """Same as recommend_personas, but also returns persona_reasoning strings.

    Each string is one human-readable line per fired rule, e.g.:
      "[primary] founder — Company appears to have fewer than 50 employees; ..."
    """
    rules = _persona_rules()
    positive_signals = {s.signal for s in signal_scores if s.points > 0}

    personas: list[PersonaRecommendation] = []
    reasoning: list[str] = []

    def _apply(rule_kind: str, rule: dict[str, Any]) -> None:
        if not _evaluate_condition(
            rule.get("condition", {}),
            employee_count_estimate=employee_count_estimate,
            score=score,
            positive_signals=positive_signals,
        ):
            return
        key = rule.get("persona")
        if not key:
            return
        persona = _build_persona(key)
        if "override_why" in rule:
            persona = PersonaRecommendation(
                persona=persona.persona,
                titles=persona.titles,
                why=rule["override_why"],
                priority=int(rule.get("override_priority", persona.priority)),
            )
        personas.append(persona)
        reason = rule.get("reason", "")
        if reason:
            reasoning.append(f"[{rule_kind}] {key} — {reason}")

    # Primary: stop at the first matching rule so primary stays unique.
    for rule in rules.get("primary", []) or []:
        if _evaluate_condition(
            rule.get("condition", {}),
            employee_count_estimate=employee_count_estimate,
            score=score,
            positive_signals=positive_signals,
        ):
            _apply("primary", rule)
            break

    for rule in rules.get("secondary", []) or []:
        _apply("secondary", rule)

    for rule in rules.get("fallback", []) or []:
        _apply("fallback", rule)

    # Dedupe by persona name, keeping the highest priority instance.
    deduped: dict[PersonaName, PersonaRecommendation] = {}
    for persona in personas:
        existing = deduped.get(persona.persona)
        if not existing or persona.priority > existing.priority:
            deduped[persona.persona] = persona

    ranked = sorted(deduped.values(), key=lambda p: p.priority, reverse=True)[:5]
    return ranked, reasoning
