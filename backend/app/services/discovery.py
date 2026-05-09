from __future__ import annotations

from app.core.domain import normalize_domain
from app.providers.exa import ExternalCallsDisabled, discover_with_exa
from app.schemas import DiscoveryCandidate

FALLBACK_CANDIDATES = [
    ("Merge", "merge.dev", "Unified API company with obvious integration surface."),
    ("Paragon", "useparagon.com", "Embedded integrations platform; strong reference for integration language."),
    ("Nylas", "nylas.com", "API platform for communications workflows."),
    ("Sensible", "sensible.so", "Document automation product likely feeding customer systems."),
    ("OpenSpace", "openspace.ai", "Construction workflow platform with integration-heavy customer base."),
    ("Buildots", "buildots.com", "Construction AI progress tracking requiring project-system sync."),
    ("Retell AI", "retellai.com", "Voice agents often need CRM, support, and workflow integrations."),
    ("Artisan", "artisan.co", "AI sales workflows likely need CRM and sequence integrations."),
]


async def discover_candidates(query: str, limit: int = 25, dry_run: bool = True) -> list[DiscoveryCandidate]:
    if not dry_run:
        try:
            return await discover_with_exa(query, limit=limit)
        except ExternalCallsDisabled:
            raise

    candidates = [
        DiscoveryCandidate(name=name, domain=normalize_domain(domain), url=f"https://{domain}", reason=reason, source="fallback_seed")
        for name, domain, reason in FALLBACK_CANDIDATES
    ]
    return candidates[:limit]
