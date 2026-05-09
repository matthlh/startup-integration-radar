from __future__ import annotations

from app.schemas import PersonaName, PersonaRecommendation, SignalName, SignalScore

FOUNDER_PERSONA = PersonaRecommendation(
    persona=PersonaName.founder,
    titles=["Founder", "CEO", "Co-founder"],
    why="Company appears to be under 50 people, so the founder is most likely to own integration tradeoffs directly.",
    priority=5,
)

PRODUCT_PERSONA = PersonaRecommendation(
    persona=PersonaName.product,
    titles=["Head of Product", "VP Product", "Product Lead", "Product Manager, Integrations"],
    why="Company appears to be over 50 people, so product likely owns roadmap tradeoffs when integrations block deals.",
    priority=5,
)

PARTNERSHIPS_PERSONA = PersonaRecommendation(
    persona=PersonaName.partnerships,
    titles=["Head of Partnerships", "Partnerships Lead", "Ecosystem Lead"],
    why="Company appears to be over 50 people, so partnerships may own integration coverage and ecosystem expansion.",
    priority=4,
)


def select_primary_persona(employee_count_estimate: int | None) -> PersonaRecommendation:
    """Checklist persona rule.

    - < 50 people: target Founder.
    - > 50 people: target Head of Product / Partnerships. Product is primary,
      Partnerships is added as secondary by recommend_personas().
    - Unknown or exactly 50: use Product as the scalable default but keep
      Founder in the recommendation list for validation.
    """
    if employee_count_estimate is not None and employee_count_estimate < 50:
        return FOUNDER_PERSONA
    return PRODUCT_PERSONA


def recommend_personas(
    signal_scores: list[SignalScore],
    score: int,
    employee_count_estimate: int | None = None,
) -> list[PersonaRecommendation]:
    primary = select_primary_persona(employee_count_estimate)
    positive = {s.signal for s in signal_scores if s.points > 0}
    personas: list[PersonaRecommendation] = [primary]

    if employee_count_estimate is not None and employee_count_estimate > 50:
        personas.append(PARTNERSHIPS_PERSONA)

    if SignalName.integration_language in positive or SignalName.customer_system_complexity in positive:
        personas.append(PRODUCT_PERSONA)
        personas.append(PARTNERSHIPS_PERSONA)

    if SignalName.developer_surface in positive or SignalName.implementation_burden in positive:
        personas.append(
            PersonaRecommendation(
                persona=PersonaName.engineering,
                titles=["CTO", "Head of Engineering", "Engineering Manager, Platform", "Integrations Lead"],
                why="Engineering feels the maintenance cost of one-off customer integrations.",
                priority=4,
            )
        )
        personas.append(
            PersonaRecommendation(
                persona=PersonaName.solutions,
                titles=["Head of Solutions", "Solutions Engineering Lead", "Implementation Lead"],
                why="Solutions teams see integration friction during onboarding and enterprise pilots.",
                priority=4,
            )
        )

    if employee_count_estimate is None or score < 70:
        personas.append(
            PersonaRecommendation(
                persona=PersonaName.founder,
                titles=["Founder", "CEO", "Co-founder"],
                why="Use founder outreach to validate whether integration pain is a real priority when company size is unknown or public signals are weaker.",
                priority=3,
            )
        )

    deduped: dict[PersonaName, PersonaRecommendation] = {}
    for persona in personas:
        existing = deduped.get(persona.persona)
        if not existing or persona.priority > existing.priority:
            deduped[persona.persona] = persona
    return sorted(deduped.values(), key=lambda item: item.priority, reverse=True)[:5]
