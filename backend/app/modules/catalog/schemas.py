from datetime import date

from pydantic import BaseModel, ConfigDict


class RequirementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    degree_level: str
    sat_min: int | None = None
    sat_p25: int | None = None
    sat_p75: int | None = None
    sat_required: str | None = None
    ielts_min: float | None = None
    toefl_ibt_min: int | None = None
    gpa_min: float | None = None
    extracurriculars_weight: str | None = None
    notes_ru: str | None = None
    extra: dict | None = None
    data_source: str
    source_url: str | None = None
    last_verified_at: date | None = None


class CostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    degree_level: str
    cost_type: str
    amount: float
    currency: str
    amount_usd: float | None = None
    academic_year: str | None = None
    data_source: str
    source_url: str | None = None
    last_verified_at: date | None = None


class DeadlineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    degree_level: str
    round_name: str
    deadline_date: date
    intake_term: str | None = None
    data_source: str
    source_url: str | None = None
    last_verified_at: date | None = None


class UniversityCard(BaseModel):
    """Карточка в выдаче поиска."""

    id: int
    slug: str
    name_en: str
    name_ru: str | None = None
    country_code: str
    city: str | None = None
    logo_url: str | None = None
    tuition_usd: float | None = None
    application_fee_usd: float | None = None
    sat_p25: int | None = None
    sat_p75: int | None = None
    ielts_min: float | None = None
    next_deadline: date | None = None
    requirements_unknown: bool = False  # бейдж «требования уточняйте на сайте»
    last_verified_at: date | None = None


class SearchResponse(BaseModel):
    items: list[UniversityCard]
    total: int
    page: int
    per_page: int


class UniversityDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name_en: str
    name_ru: str | None = None
    country_code: str
    city: str | None = None
    website_url: str | None = None
    apply_url: str | None = None
    application_system: str | None = None
    logo_url: str | None = None
    description_ru: str | None = None
    rankings: dict | None = None
    data_source: str
    source_url: str | None = None
    last_verified_at: date | None = None
    requirements: list[RequirementOut] = []
    costs: list[CostOut] = []
    deadlines: list[DeadlineOut] = []


class FilterMeta(BaseModel):
    countries: list[str]
    degree_levels: list[str]
    tuition_usd_min: float | None = None
    tuition_usd_max: float | None = None


class OutboundClickIn(BaseModel):
    university_id: int
    target_url: str
