# Модель данных

Реализация: `backend/app/modules/*/models.py`. Здесь — схема и решения, стоящие за ней.

## Принципы

1. **Свежесть — колонка первого класса.** Анализ конкурентов показал: устаревшие данные убили доверие ко всем. Каждая таблица с фактами несёт `data_source`, `source_url`, `last_verified_at`; UI показывает «проверено N дней назад».
2. **Оригинальная валюта — всегда.** Конверсии протухают, исходные цифры — нет. `amount` + `currency` хранятся как на сайте вуза, `amount_usd` — денормализованное поле, пересчитываемое скриптом курсов еженедельно. Фильтр по бюджету бежит по `amount_usd`, UI показывает оригинал + ≈USD/₸ с датой курса.
3. **Компромисс гранулярности требований.** Реальность: «требования различаются по программам». Но курировать пер-программно 300 вузов соло невозможно. Решение: требования привязаны к `(university, degree_level)` как дефолт + опциональный `program_id` для исключений. UI пишет: «типично для бакалавриата; отдельные программы могут отличаться» + ссылка наружу. Схема готова к пер-программной глубине без миграций — просто больше строк.
4. **Черновики и публикация.** `is_published=false` для всего, что пришло из автоматических источников. Публикация — только после ручной проверки.
5. **i18n парными колонками** (`name_en`/`name_ru`, `description_ru`), а не таблицей переводов — проще; казахский добавится колонками `_kk`.

## Таблицы

### universities
| Поле | Тип | Назначение |
|---|---|---|
| id | PK | |
| slug | text UNIQUE | `mit`, `kaist` — человекочитаемый URL |
| name_en, name_ru | text | официальное название + русский перевод |
| aliases | JSON (список) | «Гарвард», «Havard», «каист» — русские написания и опечатки для поиска |
| country_code | char(2) | ISO 3166-1 |
| city | text | |
| website_url | text | главный сайт |
| **apply_url** | text | **прямая ссылка на портал подачи — самое ценное поле продукта** |
| application_system | text | `common_app` / `ucas` / `direct` |
| logo_url, description_ru | text | описание пишем своими словами (копирайт!) |
| rankings | JSON | `{"qs": 145}` — только номер + ссылка наружу, таблицы рейтингов не воспроизводим (лицензия QS/THE) |
| external_ids | JSON | `{"scorecard_id": 166027}` — ключи upsert'а для импортёров |
| is_published | bool | workflow курации |
| data_source / source_url / last_verified_at | | паттерн свежести |

### admission_requirements
Привязка: `university_id` + `degree_level` (+ `program_id` NULL = дефолт вуза). UNIQUE по этой тройке.

| Поле | Комментарий |
|---|---|
| sat_min, sat_p25, sat_p75 | минимум и диапазон поступивших (p25/p75 приходят из College Scorecard) |
| sat_required | `required` / `optional` / `not_used` — в США сейчас много test-optional |
| ielts_min (numeric 2,1), toefl_ibt_min | минимумы для admission (не для стипендий) |
| gpa_min | numeric(3,2) |
| extracurriculars_weight | `none` / `considered` / `important` |
| notes_ru | нюансы одной-двумя фразами («нужен Foundation-год») |
| extra | JSON — страновые особенности: `{"ent_accepted": true, "topik_level": 3}` |

**NULL-семантика:** `sat_min IS NULL` = «неизвестно/не требуется». При фильтрации такой вуз **проходит** фильтр, но получает бейдж «требования уточняйте на сайте». Не скрываем — честно помечаем.

### costs
`university_id` + `degree_level` + `cost_type` (UNIQUE). Типы: `tuition_year`, `application_fee`, `living_estimate_year`.
`amount` + `currency` (оригинал) + `amount_usd` (пересчёт) + `academic_year` ('2026/27').

### deadlines
`university_id` + `degree_level` + `round_name` ('Early Action' / 'Regular' / 'Fall intake') + `deadline_date` + `intake_term` ('Fall 2027'). Индекс по `deadline_date` — для напоминаний фазы 2.

### programs (в MVP почти пустая)
Только для исключений/флагманских программ. `degree_level`: `bachelor` / `master` / `phd` / `foundation`.

### profiles
`user_id` (UUID = Supabase `auth.users.id`, Supabase ведёт auth-таблицы сам) + баллы (sat/ielts/toefl/gpa) + `budget_usd_year` + `target_degree`.
Смысл: «заполнил один раз — фильтруешь всегда» — крючок удержания.

### favorites
Композитный PK `(user_id, university_id)`. До логина избранное живёт в localStorage; при первом логине мёрджится эндпоинтом `POST /me/favorites/merge`.

### outbound_clicks
Каждый клик по apply-ссылке: `university_id`, `user_id` (nullable — анонимы ок), `target_url`, `clicked_at`.
Это ключевая метрика ценности и будущая база прайсинга спонсорских профилей — храним у себя, не отдаём только в аналитику.

### currency_rates
`currency` PK, `usd_per_unit`, `fetched_at`. Обновляется `update_fx.py` еженедельно (open.er-api.com, бесплатно).

## Индексы

- `universities`: GIN trigram по `name_en` (+ tsvector в Postgres), индексы по `country_code`, `is_published`
- `admission_requirements(degree_level, sat_min, ielts_min)` — под eligibility-фильтр
- `costs(cost_type, amount_usd)` — под фильтр бюджета
- `deadlines(deadline_date)` — под напоминания
- RLS на `favorites`/`profiles` в Supabase как defense-in-depth (доступ и так через FastAPI)

## Portability: SQLite (dev) ↔ Postgres (prod)

- `degree_level` хранится строкой (не Postgres ENUM) — работает в обеих БД.
- JSON вместо JSONB/ARRAY в моделях; сериализация с `ensure_ascii=False` (иначе русские алиасы хранятся эскейпами и поиск по ним ломается — уже наступали).
- Специфика Postgres (pg_trgm, tsvector GENERATED, RLS) добавляется отдельной миграцией, помеченной «Postgres-only».
