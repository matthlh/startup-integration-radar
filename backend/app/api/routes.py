from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from app.config import get_settings
from app.schemas import AnalyzeBatchRequest, AnalyzeCompanyRequest, CompanyProfile, DiscoveryRequest
from app.services.discovery import discover_candidates
from app.services.exporter import companies_to_csv, filter_companies
from app.services.profiler import profile_company
from app.services.seed_manager import (
    SeedRow,
    add_seed,
    list_seeds,
    remove_seed,
)
from app.storage.json_store import CompanyStore


class ReviewStatusUpdate(BaseModel):
    review_status: Literal["new", "approved", "skip", "needs_research"]


class SeedCreate(BaseModel):
    domain: str
    company_name: str = ""
    category: str = ""
    notes: str = ""

router = APIRouter()
store = CompanyStore()


@router.get("/health")
async def health() -> dict:
    """Healthcheck used by Render/Railway and the dashboard.

    Returns service name, storage path, and version so smoke-testing a hosted
    deployment is one curl call away.
    """
    settings = get_settings()
    return {
        "ok": True,
        "service": "integration-scout",
        "storage": settings.data_dir,
        "version": "0.3.0",
        "external_calls_enabled": settings.enable_external_api_calls,
    }


@router.post("/discover")
async def discover(request: DiscoveryRequest):
    return {
        "query": request.query,
        "seed_company": request.seed_company,
        "dry_run": request.dry_run,
        "results": await discover_candidates(request.query, limit=request.limit, dry_run=request.dry_run),
    }


@router.post("/analyze", response_model=CompanyProfile)
async def analyze_company(request: AnalyzeCompanyRequest):
    profile = await profile_company(request.domain, use_llm=request.use_llm)
    if request.save:
        store.upsert(profile)
    return profile


@router.post("/analyze/batch")
async def analyze_batch(request: AnalyzeBatchRequest):
    results = []
    for domain in request.domains:
        profile = await profile_company(domain, use_llm=request.use_llm)
        if request.save:
            store.upsert(profile)
        results.append(profile)
    return {"count": len(results), "results": results}


@router.get("/companies")
async def list_companies():
    return store.list()


@router.get("/companies/{domain}", response_model=CompanyProfile)
async def get_company(domain: str):
    profile = store.get(domain)
    if not profile:
        raise HTTPException(status_code=404, detail="Company not found")
    return profile


@router.get("/seeds")
async def list_seed_rows():
    return [row.to_dict() for row in list_seeds()]


@router.post("/seeds")
async def add_seed_row(seed: SeedCreate):
    try:
        row, added = add_seed(
            domain=seed.domain,
            company_name=seed.company_name,
            category=seed.category,
            notes=seed.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"row": row.to_dict(), "added": added}


@router.delete("/seeds/{domain}")
async def delete_seed_row(domain: str):
    removed = remove_seed(domain)
    if removed is None:
        raise HTTPException(status_code=404, detail="Seed not found")
    return {"removed": removed.to_dict()}


@router.patch("/companies/{domain}/review_status", response_model=CompanyProfile)
async def set_review_status(domain: str, update: ReviewStatusUpdate):
    profile = store.get(domain)
    if not profile:
        raise HTTPException(status_code=404, detail="Company not found")
    profile.review_status = update.review_status
    store.upsert(profile)
    return profile


@router.get("/exports/clay.csv", response_class=PlainTextResponse)
async def export_clay_csv(
    status: str | None = Query(
        default=None,
        description="Filter by review_status (e.g. 'approved'). Omit to export all.",
    ),
):
    profiles = filter_companies(store.list(), status=status)
    return PlainTextResponse(companies_to_csv(profiles), media_type="text/csv")
