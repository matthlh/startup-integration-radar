"""Tests for the config-driven persona routing rules.

Persona logic is loaded from `backend/config/signals.yaml` so the operator
can retarget without editing Python.
"""

from app.schemas import SignalName, SignalScore
from app.services.persona import (
    recommend_personas,
    recommend_personas_with_reasoning,
    select_primary_persona,
)


def _signal(name: SignalName, points: int = 10, max_points: int = 15) -> SignalScore:
    return SignalScore(signal=name, points=points, max_points=max_points)


# ─── Headcount-driven primary ────────────────────────────────────────────────

def test_under_50_employees_picks_founder():
    primary = select_primary_persona(25)
    assert primary.persona.value == "founder"

    personas = recommend_personas([], score=80, employee_count_estimate=25)
    assert personas[0].persona.value == "founder"


def test_over_50_employees_picks_product():
    primary = select_primary_persona(120)
    assert primary.persona.value == "product"

    personas = recommend_personas([], score=80, employee_count_estimate=120)
    assert personas[0].persona.value == "product"
    # 50+ size auto-adds partnerships.
    assert any(p.persona.value == "partnerships" for p in personas)


def test_unknown_employee_count_defaults_to_product_with_founder_fallback():
    primary = select_primary_persona(None)
    assert primary.persona.value == "product"

    personas = recommend_personas([], score=60, employee_count_estimate=None)
    persona_names = [p.persona.value for p in personas]
    assert persona_names[0] == "product"
    # Founder must still be in the list as a fallback for size-unknown leads.
    assert "founder" in persona_names


# ─── Signal-driven additions ─────────────────────────────────────────────────

def test_partnership_signal_adds_partnerships_persona():
    """Partnership/ecosystem language should add Partnerships even at small companies."""
    signals = [_signal(SignalName.partner_ecosystem, points=4, max_points=5)]
    personas = recommend_personas(signals, score=72, employee_count_estimate=20)
    assert any(p.persona.value == "partnerships" for p in personas)
    # Primary stays founder under threshold.
    assert personas[0].persona.value == "founder"


def test_integration_language_signal_adds_partnerships():
    signals = [_signal(SignalName.integration_language, points=15, max_points=15)]
    personas = recommend_personas(signals, score=80, employee_count_estimate=30)
    assert any(p.persona.value == "partnerships" for p in personas)


def test_developer_surface_signal_adds_engineering_persona():
    """API/SDK/webhook/developer language should add Engineering."""
    signals = [_signal(SignalName.developer_surface, points=12, max_points=15)]
    personas = recommend_personas(signals, score=82, employee_count_estimate=20)
    assert any(p.persona.value == "engineering" for p in personas)


def test_implementation_burden_signal_also_adds_engineering_and_solutions():
    signals = [_signal(SignalName.implementation_burden, points=10, max_points=10)]
    personas = recommend_personas(signals, score=75, employee_count_estimate=120)
    persona_names = {p.persona.value for p in personas}
    assert "engineering" in persona_names
    assert "solutions" in persona_names


# ─── Persona reasoning output ────────────────────────────────────────────────

def test_persona_reasoning_explains_each_added_persona():
    signals = [
        _signal(SignalName.developer_surface, points=12, max_points=15),
        _signal(SignalName.partner_ecosystem, points=4, max_points=5),
    ]
    personas, reasoning = recommend_personas_with_reasoning(
        signals, score=82, employee_count_estimate=120
    )
    # Every line should explain who and why.
    assert all(line.startswith("[") for line in reasoning)
    joined = " ".join(reasoning).lower()
    assert "product" in joined
    assert "engineering" in joined
    assert "partnerships" in joined
    # Mark whether each line was a primary, secondary, or fallback decision.
    assert any("[primary]" in line for line in reasoning)
    assert any("[secondary]" in line for line in reasoning)


def test_persona_reasoning_includes_unknown_size_fallback():
    """When size is unknown, reasoning should mention the unknown-size founder fallback."""
    _, reasoning = recommend_personas_with_reasoning(
        [], score=82, employee_count_estimate=None
    )
    joined = " ".join(reasoning).lower()
    assert "unknown" in joined or "founder" in joined
