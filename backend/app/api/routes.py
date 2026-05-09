from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from app.schemas import AnalyzeBatchRequest, AnalyzeCompanyRequest, CompanyProfile, DiscoveryRequest
from app.services.discovery import discover_candidates
from app.services.exporter import companies_to_csv
from app.services.profiler import profile_company
from app.storage.json_store import CompanyStore

router = APIRouter()
store = CompanyStore()


@router.get("/health")
async def health() -> dict:
    return {"ok": True, "service": "integration-radar"}


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


@router.get("/exports/clay.csv", response_class=PlainTextResponse)
async def export_clay_csv():
    return PlainTextResponse(companies_to_csv(store.list()), media_type="text/csv")
