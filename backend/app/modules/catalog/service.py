from datetime import date

from sqlalchemy import String, and_, cast, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.modules.catalog.models import AdmissionRequirement, Cost, Deadline, University
from app.modules.catalog.schemas import SearchResponse, UniversityCard


def search_universities(
    db: Session,
    *,
    q: str | None = None,
    countries: list[str] | None = None,
    degree_level: str = "bachelor",
    max_tuition_usd: float | None = None,
    max_app_fee_usd: float | None = None,
    sat: int | None = None,
    ielts: float | None = None,
    deadline_after: date | None = None,
    sort: str = "name",
    page: int = 1,
    per_page: int = 20,
) -> SearchResponse:
    stmt = select(University).where(University.is_published.is_(True))

    if q:
        pattern = f"%{q.strip()}%"
        # В Postgres сюда добавится pg_trgm similarity (см. план §7);
        # cast(aliases) — грубый, но рабочий поиск по русским алиасам в JSON.
        stmt = stmt.where(
            or_(
                University.name_en.ilike(pattern),
                University.name_ru.ilike(pattern),
                University.city.ilike(pattern),
                cast(University.aliases, String).ilike(pattern),
            )
        )
    if countries:
        stmt = stmt.where(University.country_code.in_([c.upper() for c in countries]))

    req = AdmissionRequirement
    req_conditions = [req.university_id == University.id, req.degree_level == degree_level]
    # NULL-минимум проходит фильтр: не скрываем вуз, а показываем бейдж «уточняйте» (план §6)
    if sat is not None:
        req_conditions.append(or_(req.sat_min.is_(None), req.sat_min <= sat))
    if ielts is not None:
        req_conditions.append(or_(req.ielts_min.is_(None), req.ielts_min <= ielts))
    if sat is not None or ielts is not None:
        stmt = stmt.where(select(req.id).where(and_(*req_conditions)).exists())

    if max_tuition_usd is not None:
        stmt = stmt.where(
            select(Cost.id)
            .where(
                Cost.university_id == University.id,
                Cost.degree_level == degree_level,
                Cost.cost_type == "tuition_year",
                Cost.amount_usd <= max_tuition_usd,
            )
            .exists()
        )
    if max_app_fee_usd is not None:
        stmt = stmt.where(
            select(Cost.id)
            .where(
                Cost.university_id == University.id,
                Cost.degree_level == degree_level,
                Cost.cost_type == "application_fee",
                Cost.amount_usd <= max_app_fee_usd,
            )
            .exists()
        )
    if deadline_after is not None:
        stmt = stmt.where(
            select(Deadline.id)
            .where(
                Deadline.university_id == University.id,
                Deadline.degree_level == degree_level,
                Deadline.deadline_date >= deadline_after,
            )
            .exists()
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    tuition_subq = (
        select(Cost.amount_usd)
        .where(
            Cost.university_id == University.id,
            Cost.degree_level == degree_level,
            Cost.cost_type == "tuition_year",
        )
        .scalar_subquery()
    )
    if sort == "tuition_asc":
        stmt = stmt.order_by(tuition_subq.asc().nulls_last())
    elif sort == "deadline_asc":
        next_deadline_subq = (
            select(func.min(Deadline.deadline_date))
            .where(Deadline.university_id == University.id, Deadline.degree_level == degree_level)
            .scalar_subquery()
        )
        stmt = stmt.order_by(next_deadline_subq.asc().nulls_last())
    else:
        stmt = stmt.order_by(University.name_en.asc())

    stmt = stmt.options(
        selectinload(University.requirements),
        selectinload(University.costs),
        selectinload(University.deadlines),
    ).offset((page - 1) * per_page).limit(per_page)

    unis = db.scalars(stmt).all()
    items = [_to_card(u, degree_level) for u in unis]
    return SearchResponse(items=items, total=total, page=page, per_page=per_page)


def _to_card(u: University, degree_level: str) -> UniversityCard:
    req = next((r for r in u.requirements if r.degree_level == degree_level and r.program_id is None), None)
    tuition = next(
        (c for c in u.costs if c.degree_level == degree_level and c.cost_type == "tuition_year"), None
    )
    app_fee = next(
        (c for c in u.costs if c.degree_level == degree_level and c.cost_type == "application_fee"), None
    )
    future = [d.deadline_date for d in u.deadlines if d.degree_level == degree_level and d.deadline_date >= date.today()]
    return UniversityCard(
        id=u.id,
        slug=u.slug,
        name_en=u.name_en,
        name_ru=u.name_ru,
        country_code=u.country_code,
        city=u.city,
        logo_url=u.logo_url,
        tuition_usd=float(tuition.amount_usd) if tuition and tuition.amount_usd is not None else None,
        application_fee_usd=float(app_fee.amount_usd) if app_fee and app_fee.amount_usd is not None else None,
        sat_p25=req.sat_p25 if req else None,
        sat_p75=req.sat_p75 if req else None,
        ielts_min=float(req.ielts_min) if req and req.ielts_min is not None else None,
        next_deadline=min(future) if future else None,
        requirements_unknown=req is None or (req.sat_min is None and req.ielts_min is None),
        last_verified_at=u.last_verified_at,
    )


def get_university_by_slug(db: Session, slug: str) -> University | None:
    stmt = (
        select(University)
        .where(University.slug == slug, University.is_published.is_(True))
        .options(
            selectinload(University.requirements),
            selectinload(University.costs),
            selectinload(University.deadlines),
        )
    )
    return db.scalars(stmt).first()
