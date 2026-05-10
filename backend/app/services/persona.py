from __future__ import annotations

from app.core.signal_rules import get_config
from app.schemas import PersonaName, PersonaRecommendation, SignalName, SignalScore


def _build_persona(key: str) -> PersonaRecommendation:
    """Build a PersonaRecommendation from the signals.yaml personas config."""
    cfg = get_config().get("personas", {}).get(key, {})
    return PersonaRecommendation(
        persona=PersonaName(key),
        titles=cfg.get("titles", [key.title()]),
        why=cfg.get("why", ""),
        priority=cfg.get("priority", 3),
    )


def _threshold() -> int:
    return int(get_config().get("personas", {}).get("small_company_threshold", 50))


def select_primary_persona(employee_count_estimate: int | None) -> PersonaRecommendation:
    """Return the primary persona based on estimated headcount.

    - Below threshold → Founder
    - At or above threshold, or unknown → Product
    """
    if employee_count_estimate is not None and employee_count_estimate < _threshold():
        return _build_persona("founder")
    return _build_persona("product")


def recommend_personas(
    signal_scores: list[SignalScore],
    score: int,
    employee_count_estimate: int | None = None,
) -> list[PersonaRecommendation]:
    primary = select_primary_persona(employee_count_estimate)
    positive = {s.signal for s in signal_scores if s.points > 0}
    personas: list[PersonaRecommendation] = [primary]

    if employee_count_estimate is not None and employee_count_estimate >= _threshold():
        personas.append(_build_persona("partnerships"))

    if SignalName.integration_language in positive or SignalName.customer_system_complexity in positive:
        personas.append(_build_persona("product"))
        personas.append(_build_persona("partnerships"))

    if SignalName.developer_surface in positive or SignalName.implementation_burden in positive:
        personas.append(_build_persona("engineering"))
        personas.append(_build_persona("solutions"))

    if employee_count_estimate is None or score < 70:
        # Add founder as a validation fallback when size is unknown or signals are weaker
        fallback = _build_persona("founder")
        fallback = PersonaRecommendation(
            persona=fallback.persona,
            titles=fallback.titles,
            why="Use founder outreach to validate whether integration pain is a real priority "
                "when company size is unknown or public signals are weaker.",
            priority=3,
        )
        personas.append(fallback)

    deduped: dict[PersonaName, PersonaRecommendation] = {}
    for persona in personas:
        existing = deduped.get(persona.persona)
        if not existing or persona.priority > existing.priority:
            deduped[persona.persona] = persona
    return sorted(deduped.values(), key=lambda p: p.priority, reverse=True)[:5]
