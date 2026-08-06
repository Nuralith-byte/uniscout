"""Еженедельное обновление курсов валют + пересчёт amount_usd во всех costs.

Источник: open.er-api.com (бесплатно, без ключа).
Запуск: python -m app.ingest.update_fx  (в проде — GitHub Actions cron, он же keep-alive Supabase)
"""
import httpx
from sqlalchemy import select

from app.core.db import Base, SessionLocal, engine
from app.modules.catalog.models import Cost, CurrencyRate

API = "https://open.er-api.com/v6/latest/USD"


def run() -> None:
    Base.metadata.create_all(engine)
    resp = httpx.get(API, timeout=30)
    resp.raise_for_status()
    rates_from_usd = resp.json()["rates"]  # {"KZT": 525.3, ...} — сколько валюты за 1 USD

    db = SessionLocal()
    try:
        for code, per_usd in rates_from_usd.items():
            if not per_usd:
                continue
            rate = db.get(CurrencyRate, code)
            usd_per_unit = 1.0 / per_usd
            if rate:
                rate.usd_per_unit = usd_per_unit
            else:
                db.add(CurrencyRate(currency=code, usd_per_unit=usd_per_unit))
        db.flush()

        updated = 0
        for cost in db.scalars(select(Cost)).all():
            rate = db.get(CurrencyRate, cost.currency)
            if rate:
                cost.amount_usd = round(float(cost.amount) * float(rate.usd_per_unit), 2)
                updated += 1
        db.commit()
        print(f"Курсы обновлены ({len(rates_from_usd)} валют), пересчитано costs: {updated}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
