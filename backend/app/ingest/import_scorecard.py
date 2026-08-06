"""Обогащение американских вузов из College Scorecard API (public domain).

Ключ бесплатный: https://api.data.gov/signup/ → SCORECARD_API_KEY в окружении.
Запуск: SCORECARD_API_KEY=... python -m app.ingest.import_scorecard "Massachusetts Institute of Technology" ...
Без аргументов — обогащает все US-вузы, уже существующие в БД.
"""
import os
import sys
from datetime import date

import httpx
from sqlalchemy import select

from app.core.db import SessionLocal
from app.modules.catalog.models import AdmissionRequirement, Cost, University

API = "https://api.data.gov/ed/collegescorecard/v1/schools"
FIELDS = ",".join([
    "id",
    "school.name",
    "school.city",
    "school.school_url",
    "latest.admissions.admission_rate.overall",
    "latest.admissions.sat_scores.25th_percentile.critical_reading",
    "latest.admissions.sat_scores.75th_percentile.critical_reading",
    "latest.admissions.sat_scores.25th_percentile.math",
    "latest.admissions.sat_scores.75th_percentile.math",
    "latest.cost.tuition.out_of_state",
])


def fetch_school(client: httpx.Client, api_key: str, name: str) -> dict | None:
    resp = client.get(API, params={"api_key": api_key, "school.name": name, "fields": FIELDS, "per_page": 1})
    resp.raise_for_status()
    results = resp.json().get("results", [])
    return results[0] if results else None


def enrich(db, client: httpx.Client, api_key: str, uni: University) -> bool:
    data = fetch_school(client, api_key, uni.name_en)
    if not data:
        print(f"  не найден в Scorecard: {uni.name_en}")
        return False

    sat_p25_r = data.get("latest.admissions.sat_scores.25th_percentile.critical_reading")
    sat_p75_r = data.get("latest.admissions.sat_scores.75th_percentile.critical_reading")
    sat_p25_m = data.get("latest.admissions.sat_scores.25th_percentile.math")
    sat_p75_m = data.get("latest.admissions.sat_scores.75th_percentile.math")
    tuition = data.get("latest.cost.tuition.out_of_state")

    uni.external_ids = {**(uni.external_ids or {}), "scorecard_id": data["id"]}
    uni.data_source = "college_scorecard"
    uni.last_verified_at = date.today()

    req = db.scalars(
        select(AdmissionRequirement).where(
            AdmissionRequirement.university_id == uni.id,
            AdmissionRequirement.degree_level == "bachelor",
            AdmissionRequirement.program_id.is_(None),
        )
    ).first()
    if not req:
        req = AdmissionRequirement(university_id=uni.id, degree_level="bachelor")
        db.add(req)
    if sat_p25_r and sat_p25_m:
        req.sat_p25 = int(sat_p25_r + sat_p25_m)
    if sat_p75_r and sat_p75_m:
        req.sat_p75 = int(sat_p75_r + sat_p75_m)
    req.data_source = "college_scorecard"
    req.last_verified_at = date.today()

    if tuition:
        cost = db.scalars(
            select(Cost).where(
                Cost.university_id == uni.id,
                Cost.degree_level == "bachelor",
                Cost.cost_type == "tuition_year",
            )
        ).first()
        if not cost:
            cost = Cost(
                university_id=uni.id, degree_level="bachelor", cost_type="tuition_year",
                amount=tuition, currency="USD",
            )
            db.add(cost)
        cost.amount = tuition
        cost.currency = "USD"
        cost.amount_usd = tuition
        cost.data_source = "college_scorecard"
        cost.last_verified_at = date.today()
    return True


def run(names: list[str]) -> None:
    api_key = os.environ.get("SCORECARD_API_KEY", "DEMO_KEY")  # DEMO_KEY: 1000 req/час — хватит для проб
    db = SessionLocal()
    try:
        stmt = select(University).where(University.country_code == "US")
        if names:
            stmt = stmt.where(University.name_en.in_(names))
        unis = db.scalars(stmt).all()
        print(f"Обогащаю {len(unis)} US-вузов...")
        with httpx.Client(timeout=30) as client:
            done = sum(enrich(db, client, api_key, u) for u in unis)
        db.commit()
        print(f"Готово: {done}/{len(unis)}")
    finally:
        db.close()


if __name__ == "__main__":
    run(sys.argv[1:])
