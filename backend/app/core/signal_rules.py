from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.schemas import EvidenceType, SignalName

# ─── Config loader ────────────────────────────────────────────────────────────

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "signals.yaml"


def _load_config() -> dict[str, Any]:
    with open(_CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


_config: dict[str, Any] = _load_config()


def get_config() -> dict[str, Any]:
    """Return the parsed signals.yaml config (cached at import time)."""
    return _config


def get_company_name() -> str:
    """Return the configured company name for use in outreach templates."""
    return _config.get("your_company_name", "Your Company")


# ─── Build module-level constants from config ─────────────────────────────────

def _build_constants(
    config: dict[str, Any],
) -> tuple[
    dict[SignalName, int],
    dict[SignalName, list[str]],
    dict[SignalName, int],
]:
    signal_data = config.get("signals", {})
    max_points: dict[SignalName, int] = {}
    keywords: dict[SignalName, list[str]] = {}
    weights: dict[SignalName, int] = {}

    for name, cfg in signal_data.items():
        try:
            signal = SignalName(name)
        except ValueError:
            raise ValueError(
                f"Unknown signal '{name}' in {_CONFIG_PATH}. "
                f"Valid names: {[s.value for s in SignalName]}"
            )
        max_points[signal] = int(cfg["max_points"])
        keywords[signal] = [str(k) for k in cfg.get("keywords", [])]
        weights[signal] = int(cfg["weight"])

    return max_points, keywords, weights


SIGNAL_MAX_POINTS, SIGNAL_KEYWORDS, SIGNAL_WEIGHTS = _build_constants(_config)

# ─── Evidence type hints (classification only — not in scoring config) ─────────

KEYWORD_EVIDENCE_TYPE: dict[SignalName, EvidenceType] = {
    SignalName.developer_surface: EvidenceType.docs,
    SignalName.integration_language: EvidenceType.integrations_page,
    SignalName.urgency_or_growth: EvidenceType.funding_or_news,
    SignalName.competitor_presence: EvidenceType.integrations_page,
}

# ─── Competitor aliases (loaded from config) ──────────────────────────────────

def get_competitor_aliases() -> dict[str, list[str]]:
    """Return {display_name: [alias, ...]} from signals.yaml competitors section."""
    raw = _config.get("competitors", {})
    return {name: [str(a) for a in data.get("aliases", [])] for name, data in raw.items()}
