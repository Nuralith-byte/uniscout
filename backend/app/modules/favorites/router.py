from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user_id
from app.modules.catalog.models import University
from app.modules.catalog.schemas import UniversityCard
from app.modules.catalog.service import _to_card
from app.modules.favorites.models import Favorite

router = APIRouter(prefix="/me/favorites", tags=["favorites"])


class FavoriteIn(BaseModel):
    university_id: int


class FavoritesMergeIn(BaseModel):
    """Мёрдж localStorage-избранного в БД при первом логине."""

    university_ids: list[int]


@router.get("", response_model=list[UniversityCard])
def list_favorites(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    unis = db.scalars(
        select(University)
        .join(Favorite, Favorite.university_id == University.id)
        .where(Favorite.user_id == user_id)
        .order_by(Favorite.created_at.desc())
    ).all()
    return [_to_card(u, "bachelor") for u in unis]


@router.post("", status_code=201)
def add_favorite(
    body: FavoriteIn, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    if not db.get(University, body.university_id):
        raise HTTPException(404, "Университет не найден")
    if not db.get(Favorite, (user_id, body.university_id)):
        db.add(Favorite(user_id=user_id, university_id=body.university_id))
        db.commit()


@router.post("/merge", status_code=204)
def merge_favorites(
    body: FavoritesMergeIn, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    existing = set(
        db.scalars(select(Favorite.university_id).where(Favorite.user_id == user_id)).all()
    )
    valid_ids = set(
        db.scalars(select(University.id).where(University.id.in_(body.university_ids))).all()
    )
    for uid in valid_ids - existing:
        db.add(Favorite(user_id=user_id, university_id=uid))
    db.commit()


@router.delete("/{university_id}", status_code=204)
def remove_favorite(
    university_id: int, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    fav = db.get(Favorite, (user_id, university_id))
    if fav:
        db.delete(fav)
        db.commit()
