from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.catalog import service
from app.modules.catalog.models import Cost, OutboundClick, University
from app.modules.catalog.schemas import (
    FilterMeta,
    OutboundClickIn,
    SearchResponse,
    UniversityDetail,
)

router = APIRouter(tags=["catalog"])


@router.get("/universities", response_model=SearchResponse)
def list_universities(
    db: Session = Depends(get_db),
    q: str | None = None,
    country: str | None = Query(None, description="Коды стран через запятую: US,KR"),
    degree_level: str = "bachelor",
    max_tuition_usd: float | None = None,
    max_app_fee_usd: float | None = None,
    sat: int | None = Query(None, ge=400, le=1600),
    ielts: float | None = Query(None, ge=0, le=9),
    deadline_after: date | None = None,
    sort: str = Query("name", pattern="^(name|tuition_asc|deadline_asc)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    countries = [c for c in (country or "").split(",") if c.strip()] or None
    return service.search_universities(
        db,
        q=q,
        countries=countries,
        degree_level=degree_level,
        max_tuition_usd=max_tuition_usd,
        max_app_fee_usd=max_app_fee_usd,
        sat=sat,
        ielts=ielts,
        deadline_after=deadline_after,
        sort=sort,
        page=page,
        per_page=per_page,
    )


@router.get("/universities/{slug}", response_model=UniversityDetail)
def university_detail(slug: str, db: Session = Depends(get_db)):
    uni = service.get_university_by_slug(db, slug)
    if not uni:
        raise HTTPException(404, "Университет не найден")
    return uni


@router.get("/meta/filters", response_model=FilterMeta)
def filter_meta(db: Session = Depends(get_db)):
    countries = db.scalars(
        select(University.country_code).where(University.is_published.is_(True)).distinct()
    ).all()
    tuition_min, tuition_max = db.execute(
        select(func.min(Cost.amount_usd), func.max(Cost.amount_usd)).where(Cost.cost_type == "tuition_year")
    ).one()
    return FilterMeta(
        countries=sorted(countries),
        degree_levels=["bachelor", "master"],
        tuition_usd_min=float(tuition_min) if tuition_min is not None else None,
        tuition_usd_max=float(tuition_max) if tuition_max is not None else None,
    )


@router.post("/events/outbound-click", status_code=204)
def outbound_click(body: OutboundClickIn, request: Request, db: Session = Depends(get_db)):
    """Fire-and-forget beacon: клик по apply-ссылке — ключевая метрика ценности."""
    db.add(
        OutboundClick(
            university_id=body.university_id,
            target_url=body.target_url,
            user_id=request.headers.get("X-Debug-User"),
        )
    )
    db.commit()
