# API

Все эндпоинты под `/api/v1`. FastAPI генерирует живую документацию на `/docs` (Swagger UI). Реализация: `backend/app/modules/*/router.py`.

## Каталог (публичный)

### `GET /universities` — поиск с фильтрами
| Параметр | Пример | Смысл |
|---|---|---|
| `q` | `каист` | поиск по названию/городу/русским алиасам (ILIKE; в Postgres + pg_trgm) |
| `country` | `US,KR` | ISO-коды через запятую |
| `degree_level` | `bachelor` | по умолчанию bachelor |
| `sat` | `1350` | **мои баллы**: проходят вузы с `sat_min <= 1350` ИЛИ `sat_min IS NULL` |
| `ielts` | `7.0` | аналогично |
| `max_tuition_usd` | `30000` | бюджет на обучение в год |
| `max_app_fee_usd` | `100` | максимум за подачу |
| `deadline_after` | `2026-10-01` | «ещё успеваю подать» |
| `sort` | `name` / `tuition_asc` / `deadline_asc` | |
| `page`, `per_page` | `1`, `20` | пагинация |

Ответ: `{ items: UniversityCard[], total, page, per_page }`. Карточка содержит: название, страну/город, ≈tuition в USD, диапазон SAT p25–p75, минимум IELTS, ближайший дедлайн, флаг `requirements_unknown` (бейдж «уточняйте на сайте»), `last_verified_at`.

**Принцип eligibility-фильтра:** обычные SQL WHERE, без ML и «предсказаний шансов» в v1. Вуз с неизвестными требованиями не скрывается, а помечается — честность важнее ложной точности.

### `GET /universities/{slug}` — детальная страница
Полные требования по уровням, стоимость (оригинальная валюта + ≈USD), дедлайны, ссылки; у каждого блока — источник и дата проверки.

### `GET /meta/filters`
Справочник для UI фильтров: доступные страны, min/max tuition, уровни.

## События

### `POST /events/outbound-click`
Fire-and-forget beacon (`navigator.sendBeacon` на фронте) при клике «Подать заявку» → таблица `outbound_clicks`. Ключевая метрика ценности продукта.

## Приватные (Bearer JWT от Supabase)

| Эндпоинт | Смысл |
|---|---|
| `GET /me/profile` / `PUT /me/profile` | баллы (SAT/IELTS/TOEFL/GPA), бюджет, целевой уровень — предзаполняют фильтры |
| `GET /me/favorites` | карточки избранного |
| `POST /me/favorites` | добавить `{university_id}` |
| `POST /me/favorites/merge` | мёрдж localStorage-избранного при первом логине: `{university_ids: [...]}` |
| `DELETE /me/favorites/{university_id}` | убрать |

## Админские

### `POST /admin/import` (заголовок `X-Admin-Key`)
Триггер импорта курации из Google Sheet. Возвращает отчёт: created/updated/rejected со строками и причинами.

## Auth: как устроено

**Эндпоинтов `/auth/*` в API нет — и это осознанно.**

- Фронт общается с Supabase напрямую через `@supabase/supabase-js`: регистрация, логин (email + Google OAuth), подтверждение почты, сброс пароля — всё из коробки. Это ровно тот муторный security-sensitive код, который новичку **не надо** писать самому для прода.
- Бэкенд только **проверяет** JWT: FastAPI-dependency (~30 строк, `app/core/security.py`) валидирует подпись HS256 секретом проекта (`SUPABASE_JWT_SECRET`), audience `authenticated`, достаёт `user_id` из `sub`.
- **Dev-режим:** пока Supabase не подключён, работает заголовок `X-Debug-User: <любой-id>` — избранное и профиль тестируются локально без auth.
- Учебное упражнение (рекомендуется): пройти официальный туториал FastAPI OAuth2/JWT в отдельной ветке, чтобы понять, что Supabase делает под капотом — а в прод отдать Supabase.

CORS замкнут на домен фронта (`CORS_ORIGINS`).

## Примеры

```bash
# Корея, мой IELTS 6.5, дешевле сначала
curl 'localhost:8000/api/v1/universities?country=KR&ielts=6.5&sort=tuition_asc'

# кириллический поиск с опечаткой
curl -G 'localhost:8000/api/v1/universities' --data-urlencode 'q=каист'

# избранное в dev без Supabase
curl -X POST localhost:8000/api/v1/me/favorites \
  -H 'X-Debug-User: test-1' -H 'Content-Type: application/json' \
  -d '{"university_id": 2}'
```
