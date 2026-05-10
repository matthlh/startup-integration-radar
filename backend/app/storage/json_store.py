from __future__ import annotations

import json
from pathlib import Path

from app.config import get_settings
from app.schemas import CompanyProfile


def _default_store_path() -> Path:
    return get_settings().companies_store_path


class CompanyStore:
    def __init__(self, path: Path | None = None):
        self.path = path if path is not None else _default_store_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def list(self) -> list[CompanyProfile]:
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return [CompanyProfile.model_validate(item) for item in raw]

    def upsert(self, profile: CompanyProfile) -> CompanyProfile:
        items = self.list()
        by_domain = {item.domain: item for item in items}
        by_domain[profile.domain] = profile
        self.path.write_text(
            json.dumps([item.model_dump(mode="json") for item in by_domain.values()], indent=2),
            encoding="utf-8",
        )
        return profile

    def get(self, domain: str) -> CompanyProfile | None:
        domain = domain.replace("https://", "").replace("http://", "").split("/")[0]
        if domain.startswith("www."):
            domain = domain[4:]
        for item in self.list():
            if item.domain == domain:
                return item
        return None

    def clear(self) -> None:
        self.path.write_text("[]", encoding="utf-8")
