"""Сид скелета вузов из Hipolabs (имя/страна/домен, только черновики).

Запуск: python -m app.ingest.seed_hipolabs "United States" "South Korea" ...
Без аргументов — целевые страны по умолчанию.
"""
import re
import sys

import httpx
from sqlalchemy import select

from app.core.db import Base, SessionLocal, engine
from app.modules.catalog.models import University

API = "http://universities.hipolabs.com/search"
DEFAULT_COUNTRIES = [
    "United States", "United Kingdom", "Canada", "Germany",
    "South Korea", "Japan", "China", "Turkey", "Hong Kong",
]
COUNTRY_CODES = {
    "United States": "US", "United Kingdom": "GB", "Canada": "CA", "Germany": "DE",
    "South Korea": "KR", "Japan": "JP", "China": "CN", "Turkey": "TR", "Hong Kong": "HK",
}


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:100]


def run(countries: list[str], limit_per_country: int = 50) -> None:
    Base.metadata.create_all(engine)
    db = SessionLocal()
    created = 0
    try:
        for country in countries:
            resp = httpx.get(API, params={"country": country}, timeout=30)
            resp.raise_for_status()
            for item in resp.json()[:limit_per_country]:
                slug = slugify(item["name"])
                if db.scalars(select(University).where(University.slug == slug)).first():
                    continue
                db.add(
                    University(
                        slug=slug,
                        name_en=item["name"],
                        country_code=COUNTRY_CODES.get(country, (item.get("alpha_two_code") or "XX")),
                        website_url=(item.get("web_pages") or [None])[0],
                        is_published=False,  # скелет — публикуется только после ручной курации
                        data_source="hipolabs",
                    )
                )
                created += 1
            db.commit()
            print(f"{country}: готово")
        print(f"Всего добавлено черновиков: {created}")
    finally:
        db.close()


if __name__ == "__main__":
    run(sys.argv[1:] or DEFAULT_COUNTRIES)
