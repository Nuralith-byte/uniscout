from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user_id
from app.modules.users.models import Profile

router = APIRouter(prefix="/me", tags=["users"])


class ProfileIn(BaseModel):
    sat_score: int | None = Field(None, ge=400, le=1600)
    ielts_score: float | None = Field(None, ge=0, le=9)
    toefl_score: int | None = Field(None, ge=0, le=120)
    gpa: float | None = Field(None, ge=0, le=5)
    budget_usd_year: int | None = Field(None, ge=0)
    target_degree: str | None = None


class ProfileOut(ProfileIn):
    model_config = ConfigDict(from_attributes=True)


@router.get("/profile", response_model=ProfileOut)
def get_profile(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    profile = db.get(Profile, user_id)
    return profile or ProfileOut()


@router.put("/profile", response_model=ProfileOut)
def put_profile(
    body: ProfileIn, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    profile = db.get(Profile, user_id)
    if not profile:
        profile = Profile(user_id=user_id)
        db.add(profile)
    for field, value in body.model_dump().items():
        setattr(profile, field, value)
    db.commit()
    return profile
