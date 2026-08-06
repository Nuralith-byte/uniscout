from datetime import datetime

from sqlalchemy import DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Profile(Base):
    """Профиль абитуриента: «заполнил один раз — фильтруешь всегда».

    user_id = UUID из Supabase auth.users (Supabase ведёт auth-таблицы сам).
    """

    __tablename__ = "profiles"

    user_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    sat_score: Mapped[int | None]
    ielts_score: Mapped[float | None] = mapped_column(Numeric(2, 1))
    toefl_score: Mapped[int | None]
    gpa: Mapped[float | None] = mapped_column(Numeric(3, 2))
    budget_usd_year: Mapped[int | None]
    target_degree: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
