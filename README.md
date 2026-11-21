# UniScout

Бесплатный каталог зарубежных университетов для абитуриентов из Казахстана: требования (SAT, IELTS/TOEFL), стоимость обучения и подачи, дедлайны и прямые ссылки на официальные порталы подачи. Цель — сократить поиск информации с часов до минут.

- **Репозиторий:** [github.com/Nuralith-byte/uniscout](https://github.com/Nuralith-byte/uniscout)
- **Полный план проекта (рынок, архитектура, фазы):** см. `docs/plan.md`.
- 
## Стек

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic. Модульный монолит (`app/modules/*`).
- **БД:** PostgreSQL (Supabase free tier в проде), SQLite локально — ничего ставить не нужно.
- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS 4, TanStack Query.
- **Хостинг ($0):** фронт — Vercel, API — Render free, БД+Auth — Supabase free.

## Быстрый старт (локально)

Бэкенд (терминал 1):
```bash
cd backend
/opt/homebrew/bin/python3.12 -m venv .venv        # или python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m app.ingest.seed_sample        # 10 демо-вузов
.venv/bin/uvicorn app.main:app --reload           # API: http://localhost:8000/docs
```

Фронтенд (терминал 2):
```bash
cd frontend
npm install
npm run dev                                       # сайт: http://localhost:5173
```

Всё. SQLite создаётся автоматически, запросы `/api` проксируются в бэкенд.

## Структура

```
backend/
  app/core/          конфиг, БД, проверка JWT
  app/modules/       catalog | users | favorites | admin — модульный монолит
  app/ingest/        пайплайн данных: seed_sample, seed_hipolabs, import_scorecard,
                     import_sheet (Google Sheet — источник истины курации), update_fx
  alembic/           миграции (в dev таблицы создаются автоматически)
frontend/src/        pages | components | api | lib
docs/                план проекта, гайд по курации данных
```

## Пайплайн данных

1. `python -m app.ingest.seed_sample` — демо-данные для разработки (`data_source='sample'`, цифры НЕ проверены).
2. `python -m app.ingest.seed_hipolabs` — скелет ~450 вузов по целевым странам (черновики, `is_published=false`).
3. `SCORECARD_API_KEY=... python -m app.ingest.import_scorecard` — обогащение US-вузов (SAT-диапазоны, tuition).
4. Ручная курация в Google Sheet → `python -m app.ingest.import_sheet` (см. `docs/curation_guide_ru.md`). Публикуются только проверенные вузы.
5. `python -m app.ingest.update_fx` — еженедельно, курсы валют + пересчёт `amount_usd`.

Правило №1: у каждого факта есть `data_source`, `source_url`, `last_verified_at`. Устаревшие данные = потеря доверия = смерть продукта.

## Деплой ($0)

1. **Supabase:** создать проект → Project Settings → Database → connection string → `DATABASE_URL` (замени `postgres://` на `postgresql+psycopg://`). Прогнать `alembic upgrade head`.
2. **Render:** новый Web Service из репо, root `backend`, build `pip install -r requirements.txt`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Env: `ENV=prod`, `DATABASE_URL`, `CORS_ORIGINS=https://<твой-домен>.vercel.app`, `ADMIN_API_KEY`.Важно: холодный старт ~50 сек после простоя — фронт показывает «будим сервер».
3. **Vercel:** импорт репо, root `frontend`, env `VITE_API_URL=https://<сервис>.onrender.com`.
4. **Auth (недели 5-6):** Supabase Auth на фронте (`@supabase/supabase-js`), `SUPABASE_JWT_SECRET` в env бэкенда. До этого избранное живёт в localStorage.

## Роадмап (кратко)

- **Недели 1–8 (MVP):** каталог + фильтры «мой SAT/IELTS/бюджет» + избранное + 100 вручную проверенных вузов → запуск в студенческих Telegram-чатах.
- **Фаза 2:** калькулятор шансов (светофор по SAT p25–p75), сравнение вузов, email-напоминания о дедлайнах, казахский язык.
- **Фаза 3:** трекер заявок, отзывы поступивших, монетизация (лид-ген test-prep, спонсорские профили).
