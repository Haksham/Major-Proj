"""
SALF API Routes - Faculty Profile
Manage extended profile metadata (bio, lectures, projects, courses).
"""
import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.security import get_current_user
from app.core.database import get_db
from app.models.database import User, FacultyProfile, Designation as DBDesignation

router = APIRouter(prefix="/profile", tags=["Profile"])


class LectureItem(BaseModel):
    subject: str
    year: Optional[int] = None
    semester: Optional[str] = None
    details: Optional[str] = None


class ProjectItem(BaseModel):
    title: str
    description: Optional[str] = None
    funding_source: Optional[str] = None
    funding_amount: Optional[str] = None
    status: Optional[str] = None  # ongoing | completed | planned
    year_start: Optional[int] = None
    year_end: Optional[int] = None


class CourseItem(BaseModel):
    name: str
    year: Optional[int] = None
    semester: Optional[str] = None
    students_count: Optional[int] = None


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    designation: Optional[str] = None
    years_experience: Optional[int] = None
    bio: Optional[str] = None
    lectures: Optional[List[LectureItem]] = None
    projects: Optional[List[ProjectItem]] = None
    courses: Optional[List[CourseItem]] = None


def _build_response(user: User, profile: Optional[FacultyProfile]) -> dict:
    return {
        "name": user.name,
        "email": user.email,
        "employee_id": user.employee_id,
        "designation": user.designation.value if user.designation else None,
        "role": user.role.value,
        "years_experience": profile.years_experience if profile else None,
        "bio": profile.bio if profile else None,
        "lectures": json.loads(profile.lectures_json or "[]") if profile else [],
        "projects": json.loads(profile.projects_json or "[]") if profile else [],
        "courses": json.loads(profile.courses_json or "[]") if profile else [],
    }


@router.get("/me")
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = (await db.execute(
        select(User).where(User.wallet_address == current_user["address"])
    )).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    profile = (await db.execute(
        select(FacultyProfile).where(FacultyProfile.user_id == user.id)
    )).scalar_one_or_none()

    return _build_response(user, profile)


@router.patch("/me")
async def update_my_profile(
    body: ProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = (await db.execute(
        select(User).where(User.wallet_address == current_user["address"])
    )).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if body.name is not None:
        user.name = body.name.strip()
    if body.designation is not None:
        try:
            user.designation = DBDesignation(body.designation)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid designation: {body.designation}")

    profile = (await db.execute(
        select(FacultyProfile).where(FacultyProfile.user_id == user.id)
    )).scalar_one_or_none()
    if not profile:
        profile = FacultyProfile(user_id=user.id, lectures_json="[]", projects_json="[]", courses_json="[]")
        db.add(profile)

    if body.years_experience is not None:
        profile.years_experience = body.years_experience
    if body.bio is not None:
        profile.bio = body.bio
    if body.lectures is not None:
        profile.lectures_json = json.dumps([item.model_dump() for item in body.lectures])
    if body.projects is not None:
        profile.projects_json = json.dumps([item.model_dump() for item in body.projects])
    if body.courses is not None:
        profile.courses_json = json.dumps([item.model_dump() for item in body.courses])

    await db.commit()
    await db.refresh(user)
    if profile.id:
        await db.refresh(profile)

    return _build_response(user, profile)
