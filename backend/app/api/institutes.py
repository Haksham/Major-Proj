"""
SALF API Routes - Institutes (public read)
Public endpoints so the frontend can populate institution/department pickers
during registration without requiring authentication.
"""
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.schemas import InstitutionResponse, DepartmentResponse
from app.core.database import get_db
from app.models.database import Institution, Department

router = APIRouter(prefix="/institutes", tags=["Institutes"])


def _inst_to_response(i: Institution) -> InstitutionResponse:
    return InstitutionResponse(
        id=i.id,
        code=i.code,
        name=i.name,
        admin_address=i.admin_address,
        is_active=i.is_active,
        created_at=i.created_at or datetime.utcnow(),
    )


def _dept_to_response(d: Department) -> DepartmentResponse:
    return DepartmentResponse(
        id=d.id,
        institution_id=d.institution_id,
        code=d.code,
        name=d.name,
        hod_id=d.hod_id,
        is_active=d.is_active,
        created_at=d.created_at or datetime.utcnow(),
    )


@router.get("", response_model=List[InstitutionResponse])
async def list_institutions(db: AsyncSession = Depends(get_db)):
    """List all active institutions (public — no auth required)."""
    result = await db.execute(
        select(Institution).where(Institution.is_active == True).order_by(Institution.name)
    )
    return [_inst_to_response(i) for i in result.scalars().all()]


@router.get("/{institution_id}", response_model=InstitutionResponse)
async def get_institution(institution_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single institution by ID (public)."""
    inst = await db.get(Institution, institution_id)
    if not inst or not inst.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found.")
    return _inst_to_response(inst)


@router.get("/{institution_id}/departments", response_model=List[DepartmentResponse])
async def list_departments(institution_id: int, db: AsyncSession = Depends(get_db)):
    """List active departments for an institution (public — used during registration)."""
    inst = await db.get(Institution, institution_id)
    if not inst or not inst.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found.")

    result = await db.execute(
        select(Department)
        .where(Department.institution_id == institution_id, Department.is_active == True)
        .order_by(Department.name)
    )
    return [_dept_to_response(d) for d in result.scalars().all()]
