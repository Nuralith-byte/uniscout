from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

# degree_level хранится строкой (portable между SQLite в dev и Postgres в проде)
DEGREE_LEVELS = ("bachelor", "master", "phd", "foundation")


class University(Base):
    __tablename__ = "universities"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name_en: Mapped[str] = mapped_column(String(300))
    name_ru: Mapped[str | None] = mapped_column(String(300))
    aliases: Mapped[list | None] = mapped_column(JSON)  # ["Гарвард", "Havard"] — русские написания/опечатки
    country_code: Mapped[str] = mapped_column(String(2), index=True)
    city: Mapped[str | None] = mapped_column(String(120))
    website_url: Mapped[str | None] = mapped_column(Text)
    apply_url: Mapped[str | None] = mapped_column(Text)  # прямая ссылка на портал подачи — главное поле
    application_system: Mapped[str | None] = mapped_column(String(40))  # common_app | ucas | direct | ...
    logo_url: Mapped[str | None] = mapped_column(Text)
    description_ru: Mapped[str | None] = mapped_column(Text)
    rankings: Mapped[dict | None] = mapped_column(JSON)  # {"qs": 145} — только номер + ссылка наружу
    external_ids: Mapped[dict | None] = mapped_column(JSON)  # {"scorecard_id": 166027} — ключи upsert'а
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    data_source: Mapped[str] = mapped_column(String(40), default="manual")
    source_url: Mapped[str | None] = mapped_column(Text)
    last_verified_at: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    programs: Mapped[list["Program"]] = relationship(back_populates="university", cascade="all, delete-orphan")
    requirements: Mapped[list["AdmissionRequirement"]] = relationship(
        back_populates="university", cascade="all, delete-orphan"
    )
    costs: Mapped[list["Cost"]] = relationship(back_populates="university", cascade="all, delete-orphan")
    deadlines: Mapped[list["Deadline"]] = relationship(back_populates="university", cascade="all, delete-orphan")


class Program(Base):
    """В MVP опциональна — только для исключений/флагманских программ."""

    __tablename__ = "programs"

    id: Mapped[int] = mapped_column(primary_key=True)
    university_id: Mapped[int] = mapped_column(ForeignKey("universities.id", ondelete="CASCADE"))
    degree_level: Mapped[str] = mapped_column(String(20))
    name_en: Mapped[str] = mapped_column(String(300))
    name_ru: Mapped[str | None] = mapped_column(String(300))
    field_of_study: Mapped[str | None] = mapped_column(String(60))
    url: Mapped[str | None] = mapped_column(Text)

    university: Mapped[University] = relationship(back_populates="programs")


class AdmissionRequirement(Base):
    """Требования на уровне (university, degree_level) как дефолт;
    program_id заполняется только для исключений."""

    __tablename__ = "admission_requirements"
    __table_args__ = (
        UniqueConstraint("university_id", "degree_level", "program_id"),
        CheckConstraint("sat_required IN ('required','optional','not_used') OR sat_required IS NULL"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    university_id: Mapped[int] = mapped_column(ForeignKey("universities.id", ondelete="CASCADE"), index=True)
    program_id: Mapped[int | None] = mapped_column(ForeignKey("programs.id", ondelete="CASCADE"))
    degree_level: Mapped[str] = mapped_column(String(20), index=True)
    sat_min: Mapped[int | None]
    sat_p25: Mapped[int | None]
    sat_p75: Mapped[int | None]
    sat_required: Mapped[str | None] = mapped_column(String(20))  # required | optional | not_used
    ielts_min: Mapped[float | None] = mapped_column(Numeric(2, 1))
    toefl_ibt_min: Mapped[int | None]
    gpa_min: Mapped[float | None] = mapped_column(Numeric(3, 2))
    extracurriculars_weight: Mapped[str | None] = mapped_column(String(20))  # none | considered | important
    notes_ru: Mapped[str | None] = mapped_column(Text)
    extra: Mapped[dict | None] = mapped_column(JSON)  # {"ent_accepted": true, "topik_level": 3}
    data_source: Mapped[str] = mapped_column(String(40), default="manual")
    source_url: Mapped[str | None] = mapped_column(Text)
    last_verified_at: Mapped[date | None] = mapped_column(Date)

    university: Mapped[University] = relationship(back_populates="requirements")


class Cost(Base):
    __tablename__ = "costs"
    __table_args__ = (
        UniqueConstraint("university_id", "degree_level", "cost_type"),
        CheckConstraint("cost_type IN ('tuition_year','application_fee','living_estimate_year')"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    university_id: Mapped[int] = mapped_column(ForeignKey("universities.id", ondelete="CASCADE"), index=True)
    degree_level: Mapped[str] = mapped_column(String(20))
    cost_type: Mapped[str] = mapped_column(String(30))
    amount: Mapped[float] = mapped_column(Numeric(12, 2))  # всегда в оригинальной валюте
    currency: Mapped[str] = mapped_column(String(3))
    amount_usd: Mapped[float | None] = mapped_column(Numeric(12, 2))  # пересчитывается update_fx.py
    academic_year: Mapped[str | None] = mapped_column(String(10))  # '2026/27'
    data_source: Mapped[str] = mapped_column(String(40), default="manual")
    source_url: Mapped[str | None] = mapped_column(Text)
    last_verified_at: Mapped[date | None] = mapped_column(Date)

    university: Mapped[University] = relationship(back_populates="costs")


class Deadline(Base):
    __tablename__ = "deadlines"

    id: Mapped[int] = mapped_column(primary_key=True)
    university_id: Mapped[int] = mapped_column(ForeignKey("universities.id", ondelete="CASCADE"), index=True)
    degree_level: Mapped[str] = mapped_column(String(20))
    round_name: Mapped[str] = mapped_column(String(60))  # 'Early Action' | 'Regular' | 'Fall intake'
    deadline_date: Mapped[date] = mapped_column(Date, index=True)
    intake_term: Mapped[str | None] = mapped_column(String(20))  # 'Fall 2027'
    data_source: Mapped[str] = mapped_column(String(40), default="manual")
    source_url: Mapped[str | None] = mapped_column(Text)
    last_verified_at: Mapped[date | None] = mapped_column(Date)

    university: Mapped[University] = relationship(back_populates="deadlines")


class CurrencyRate(Base):
    __tablename__ = "currency_rates"

    currency: Mapped[str] = mapped_column(String(3), primary_key=True)
    usd_per_unit: Mapped[float] = mapped_column(Numeric(16, 8))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OutboundClick(Base):
    """Клики по apply_url — ключевая метрика ценности, храним у себя."""

    __tablename__ = "outbound_clicks"

    id: Mapped[int] = mapped_column(primary_key=True)
    university_id: Mapped[int | None] = mapped_column(ForeignKey("universities.id", ondelete="SET NULL"))
    user_id: Mapped[str | None] = mapped_column(String(36))
    target_url: Mapped[str] = mapped_column(Text)
    clicked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
