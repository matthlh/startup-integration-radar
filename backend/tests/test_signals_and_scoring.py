from app.core.scoring import score_evidence
from app.core.signals import extract_evidence
from app.schemas import Confidence, PipelineStage, SignalName


def test_extract_high_value_integration_signals():
    text = """
    Our enterprise workflow automation platform includes API docs, webhooks,
    Salesforce integration, ERP sync, onboarding support, and SOC 2 security.
    Customers use it to automate claims management and operations.
    """
    evidence = extract_evidence(text, source_url="https://example.com")
    signals = {ev.signal for ev in evidence}
    assert SignalName.developer_surface in signals
    assert SignalName.integration_language in signals
    assert SignalName.enterprise_motion in signals
    assert SignalName.customer_system_complexity in signals


def test_score_evidence_rewards_integration_heavy_company():
    text = """
    API documentation, webhooks, SDK, Salesforce integration, HubSpot sync, ERP,
    customer workflows, implementation support, enterprise security, SOC 2,
    case studies, request demo.
    """
    evidence = extract_evidence(text)
    score, confidence, signal_scores, stage, reason = score_evidence(evidence)
    assert score >= 70
    assert confidence in {Confidence.medium, Confidence.high}
    assert stage in {PipelineStage.scored, PipelineStage.outbound_ready, PipelineStage.profiled}
    assert reason == ""
    assert any(s.signal == SignalName.integration_language for s in signal_scores)


def test_evidence_fields_are_populated_from_extract_evidence():
    text = "We offer Salesforce and HubSpot integrations with full API access."
    evidence = extract_evidence(
        text,
        source_url="https://example.com/integrations",
        page_title="Integrations | Example",
    )
    assert evidence, "Expected at least one evidence item"
    named_system = next(
        (ev for ev in evidence if ev.matched_keyword.lower() in {"salesforce", "hubspot"}),
        None,
    )
    assert named_system is not None, "Expected a named-system evidence item"
    assert named_system.source_url == "https://example.com/integrations"
    assert named_system.page_title == "Integrations | Example"
    assert named_system.matched_keyword != ""
    assert named_system.source_context != ""


def test_disqualifier_penalizes_consumer_company():
    text = "mobile game consumer app personal blog"
    evidence = extract_evidence(text)
    score, confidence, signal_scores, stage, reason = score_evidence(evidence)
    assert score < 60
    assert stage == PipelineStage.disqualified
    assert reason
