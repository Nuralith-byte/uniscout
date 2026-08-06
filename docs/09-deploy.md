# Деплой на $0

Вся инфраструктура MVP — бесплатные тарифы. Момент, когда лимиты упрутся — это успех; апгрейд стоит $10–15/мес.

## Схема

```
Пользователь
   │
   ▼
Vercel (frontend, статика+CDN, без cold start)
   │  fetch VITE_API_URL
   ▼
Render free (FastAPI)  ←── GitHub Actions cron (пайплайн, еженедельно)
   │
   ▼
Supabase free (Postgres + Auth + table editor)
```

## Пошагово

### 1. Supabase (БД + Auth)
1. Создать проект на supabase.com (регион ближе к ЦА — Frankfurt/Singapore).
2. Project Settings → Database → Connection string (URI) → заменить `postgres://` на `postgresql+psycopg://` → это `DATABASE_URL`.
3. Локально прогнать миграции: `DATABASE_URL=... .venv/bin/alembic upgrade head`.
4. Позже для Auth: Project Settings → API → JWT Secret → `SUPABASE_JWT_SECRET` бэкенда; ключи `anon` — фронту.

### 2. Render (API)
1. New Web Service из GitHub-репо; Root Directory: `backend`.
2. Build: `pip install -r requirements.txt`; Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
3. Env: `ENV=prod`, `DATABASE_URL`, `CORS_ORIGINS=https://<проект>.vercel.app`, `ADMIN_API_KEY=<случайная строка>`, позже `SUPABASE_JWT_SECRET`.

### 3. Vercel (frontend)
1. Import репо; Root Directory: `frontend` (Vite определится сам).
2. Env: `VITE_API_URL=https://<сервис>.onrender.com`.

### 4. GitHub Actions (пайплайн)
Workflow уже в репо (`.github/workflows/pipeline-cron.yml`): еженедельно курсы валют + импорт Sheet. Секреты в Settings → Secrets → Actions: `DATABASE_URL`, `SHEET_CSV_URLS`.

## Ограничения free tier — честный список

| Сервис | Ограничение | Митигация |
|---|---|---|
| **Render free** | Засыпает после ~15 мин простоя; холодный старт **30–60 сек** | (а) фронт показывает «будим сервер…» на первом медленном запросе (уже в UI); (б) UptimeRobot/cron-job.org пинг каждые 10 мин в дневные часы КЗ (серая зона ToS — проверить актуальные правила); (в) лендинг и оболочка каталога всегда рендерятся мгновенно с Vercel |
| **Supabase free** | Проект **паузится после ~7 дней без активности**; 500 МБ | Еженедельный cron пайплайна = keep-alive. 500 МБ при нашем датасете (<50 МБ) — годы запаса |
| **Vercel free** | Лимиты трафика хобби-тарифа | Для MVP с запасом; альтернатива — Cloudflare Pages (безлимитная статика) |
| **GitHub Actions** | 2000 мин/мес free | пайплайн ест ~5 мин/неделю — ни о чём |
| **Resend** (фаза 2) | 100 писем/день | для напоминаний MVP хватит |

Fallback-и: Neon вместо Supabase-Postgres, Fly.io вместо Render. Всё приложение — обычный FastAPI+Postgres без вендор-локов, переезд между хостами — вечер работы.

## Чеклист прод-готовности (перед публичным запуском)

- [ ] `ENV=prod` (отключает create_all и X-Debug-User)
- [ ] `ADMIN_API_KEY` — случайный, не дефолтный
- [ ] CORS только на домен Vercel
- [ ] `alembic upgrade head` на проде; дальше схема меняется только миграциями
- [ ] Атрибуция Discover Uni в футере (когда добавим UK-данные)
- [ ] Проверить холодный старт глазами пользователя (открыть сайт после 20 мин простоя)
- [ ] Бэкап: Supabase free делает daily backup (7 дней) — для старта достаточно; экспорт Sheet = вторая копия данных курации
