"""Импорт ручной курации из Google Sheet (источник истины).

Каждая вкладка публикуется как CSV: Файл → Поделиться → Опубликовать в интернете →
выбрать вкладку → CSV → скопировать URL. URL'ы кладутся в SHEET_CSV_URLS (через запятую).

Валидация — Pydantic: невалидные строки отклоняются ГРОМКО и попадают в отчёт,
никогда не пишутся молча. Импортёр выигрывает конфликты у ручных правок в БД.

Запуск: python -m app.ingest.import_sheet  (или POST /api/v1/admin/import)
"""
import csv
import io
from datetime import date

import httpx
from pydantic import BaseModel, Field, HttpUrl, ValidationError, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import SessionLocal
from app.modules.catalog.models import AdmissionRequirement, Cost, Deadline, University


class UniversityRow(BaseModel):
    """Одна строка вкладки universities. Колонки Sheet = поля модели."""

    slug: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    name_en: str = Field(min_length=2)
    name_ru: str | None = None
    aliases: str | None = None  # через |: "Гарвард|Havard"
    country_code: str = Field(min_length=2, max_length=2)
    city: str | None = None
    website_url: HttpUrl | None = None
    apply_url: HttpUrl | None = None
    application_system: str | None = None
    description_ru: str | None = None
    is_published: bool = False
    source_url: HttpUrl | None = None
    last_verified_at: date | None = None
    curated_by: str | None = None

    # SAT/IELTS/стоимость — в MVP курируем в той же вкладке, одна строка = один вуз (bachelor)
    sat_min: int | None = Field(None, ge=400, le=1600)
    sat_p25: int | None = Field(None, ge=400, le=1600)
    sat_p75: int | None = Field(None, ge=400, le=1600)
    sat_required: str | None = None
    ielts_min: float | None = Field(None, ge=0, le=9)
    toefl_ibt_min: int | None = Field(None, ge=0, le=120)
    notes_ru: str | None = None
    tuition_amount: float | None = Field(None, ge=0)
    tuition_currency: str | None = Field(None, min_length=3, max_length=3)
    application_fee_amount: float | None = Field(None, ge=0)
    application_fee_currency: str | None = Field(None, min_length=3, max_length=3)
    deadline_regular: date | None = None
    intake_term: str | None = None

    @field_validator("sat_required")
    @classmethod
    def check_sat_required(cls, v):
        if v and v not in ("required", "optional", "not_used"):
            raise ValueError("sat_required должен быть required|optional|not_used")
        return v

    @field_validator("*", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        return None if isinstance(v, str) and not v.strip() else v


def _upsert_row(db: Session, row: UniversityRow) -> str:
    uni = db.scalars(select(University).where(University.slug == row.slug)).first()
    action = "updated" if uni else "created"
    if not uni:
        uni = University(slug=row.slug, name_en=row.name_en, country_code=row.country_code.upper())
        db.add(uni)
        db.flush()

    uni.name_en = row.name_en
    uni.name_ru = row.name_ru
    uni.aliases = row.aliases.split("|") if row.aliases else None
    uni.country_code = row.country_code.upper()
    uni.city = row.city
    uni.website_url = str(row.website_url) if row.website_url else None
    uni.apply_url = str(row.apply_url) if row.apply_url else None
    uni.application_system = row.application_system
    uni.description_ru = row.description_ru
    uni.is_published = row.is_published
    uni.data_source = "manual"
    uni.source_url = str(row.source_url) if row.source_url else None
    uni.last_verified_at = row.last_verified_at

    meta = {"data_source": "manual", "source_url": uni.source_url, "last_verified_at": row.last_verified_at}

    req = db.scalars(
        select(AdmissionRequirement).where(
            AdmissionRequirement.university_id == uni.id,
            AdmissionRequirement.degree_level == "bachelor",
            AdmissionRequirement.program_id.is_(None),
        )
    ).first() or AdmissionRequirement(university_id=uni.id, degree_level="bachelor")
    req.sat_min, req.sat_p25, req.sat_p75 = row.sat_min, row.sat_p25, row.sat_p75
    req.sat_required, req.ielts_min, req.toefl_ibt_min = row.sat_required, row.ielts_min, row.toefl_ibt_min
    req.notes_ru = row.notes_ru
    for k, v in meta.items():
        setattr(req, k, v)
    db.add(req)

    def upsert_cost(cost_type: str, amount: float | None, currency: str | None):
        if amount is None or not currency:
            return
        cost = db.scalars(
            select(Cost).where(
                Cost.university_id == uni.id, Cost.degree_level == "bachelor", Cost.cost_type == cost_type
            )
        ).first() or Cost(university_id=uni.id, degree_level="bachelor", cost_type=cost_type,
                          amount=amount, currency=currency.upper())
        cost.amount, cost.currency = amount, currency.upper()
        for k, v in meta.items():
            setattr(cost, k, v)
        db.add(cost)

    upsert_cost("tuition_year", row.tuition_amount, row.tuition_currency)
    upsert_cost("application_fee", row.application_fee_amount, row.application_fee_currency)

    if row.deadline_regular:
        dl = db.scalars(
            select(Deadline).where(
                Deadline.university_id == uni.id,
                Deadline.degree_level == "bachelor",
                Deadline.round_name == "Regular",
            )
        ).first() or Deadline(university_id=uni.id, degree_level="bachelor",
                              round_name="Regular", deadline_date=row.deadline_regular)
        dl.deadline_date, dl.intake_term = row.deadline_regular, row.intake_term
        for k, v in meta.items():
            setattr(dl, k, v)
        db.add(dl)

    return action


def import_from_urls(db: Session, urls: list[str]) -> dict:
    report = {"created": 0, "updated": 0, "rejected": []}
    for url in [u.strip() for u in urls if u.strip()]:
        resp = httpx.get(url, timeout=30, follow_redirects=True)
        resp.raise_for_status()
        reader = csv.DictReader(io.StringIO(resp.text))
        for i, raw in enumerate(reader, start=2):  # строка 1 — заголовки
            try:
                row = UniversityRow(**raw)
            except ValidationError as e:
                report["rejected"].append({"line": i, "slug": raw.get("slug"), "errors": str(e)})
                continue
            report[_upsert_row(db, row)] += 1
    db.commit()
    return report


if __name__ == "__main__":
    if not settings.sheet_csv_urls:
        raise SystemExit("SHEET_CSV_URLS не настроен — см. .env.example")
    session = SessionLocal()
    try:
        result = import_from_urls(session, settings.sheet_csv_urls.split(","))
        print(f"Создано: {result['created']}, обновлено: {result['updated']}")
        if result["rejected"]:
            print(f"ОТКЛОНЕНО строк: {len(result['rejected'])}")
            for r in result["rejected"]:
                print(f"  строка {r['line']} ({r['slug']}): {r['errors']}")
    finally:
        session.close()
