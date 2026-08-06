"""Загрузка демо-данных для локальной разработки.

Запуск из backend/:  python -m app.ingest.seed_sample
"""
import json
from datetime import date
from pathlib import Path

from sqlalchemy import select

from app.core.db import Base, SessionLocal, engine
from app.modules.catalog.models import AdmissionRequirement, Cost, Deadline, University
from app.modules.favorites import models as _f  # noqa: F401 — регистрация таблиц
from app.modules.users import models as _u  # noqa: F401

# Курсы для расчёта amount_usd в демо-данных; в реальной работе — app/ingest/update_fx.py
FALLBACK_USD_RATES = {
    "USD": 1.0, "EUR": 1.08, "GBP": 1.27, "CAD": 0.73,
    "KRW": 0.00072, "KZT": 0.0019, "TRY": 0.024, "HKD": 0.128,
}


def run() -> None:
    Base.metadata.create_all(engine)
    data = json.loads((Path(__file__).parent / "sample_data.json").read_text())
    db = SessionLocal()
    created = 0
    try:
        for u in data["universities"]:
            if db.scalars(select(University).where(University.slug == u["slug"])).first():
                continue
            uni = University(
                slug=u["slug"],
                name_en=u["name_en"],
                name_ru=u.get("name_ru"),
                aliases=u.get("aliases"),
                country_code=u["country_code"],
                city=u.get("city"),
                website_url=u.get("website_url"),
                apply_url=u.get("apply_url"),
                application_system=u.get("application_system"),
                description_ru=u.get("description_ru"),
                rankings=u.get("rankings"),
                is_published=True,
                data_source="sample",
                last_verified_at=date.today(),
            )
            req = u.get("requirements")
            if req:
                uni.requirements.append(AdmissionRequirement(data_source="sample", **req))
            for c in u.get("costs", []):
                rate = FALLBACK_USD_RATES.get(c["currency"])
                uni.costs.append(
                    Cost(
                        degree_level="bachelor",
                        amount_usd=round(c["amount"] * rate, 2) if rate else None,
                        data_source="sample",
                        **c,
                    )
                )
            for d in u.get("deadlines", []):
                uni.deadlines.append(
                    Deadline(
                        degree_level="bachelor",
                        round_name=d["round_name"],
                        deadline_date=date.fromisoformat(d["deadline_date"]),
                        intake_term=d.get("intake_term"),
                        data_source="sample",
                    )
                )
            db.add(uni)
            created += 1
        db.commit()
        print(f"Готово: добавлено {created} вузов (демо-данные, data_source='sample')")
    finally:
        db.close()


if __name__ == "__main__":
    run()
