"""
SALF API Routes - Institute Administration
Scoped to a single institution; accessible by institute_admin and master admin.
"""
from typing import List
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from pydantic import BaseModel, Field
from typing import Optional as _Opt
from app.schemas.schemas import UserResponse, UserRole, Designation, DepartmentCreate, DepartmentResponse, UserUpdate


class _DeptCreate(BaseModel):
    """Department creation payload for institute-admin — institution_id comes from JWT."""
    code: str = Field(..., min_length=2, max_length=20)
    name: str = Field(..., min_length=2, max_length=255)
    hod_wallet_address: _Opt[str] = Field(None, pattern=r"^0x[a-fA-F0-9]{40}$")
from app.core.security import get_current_user, require_institute_admin
from app.core.database import get_db
from app.models.database import User, Department, Institution, Contribution, UserRole as DBUserRole, Designation as DBDesignation
from app.services.blockchain_service import blockchain_service

router = APIRouter(prefix="/institute-admin", tags=["Institute Administration"])


def _user_to_response(u: User, blockchain_tx_hash: _Opt[str] = None) -> UserResponse:
    return UserResponse(
        id=u.id,
        wallet_address=u.wallet_address,
        name=u.name,
        email=u.email,
        employee_id=u.employee_id,
        role=UserRole(u.role.value),
        designation=Designation(u.designation.value) if u.designation else None,
        institution_id=u.institution_id,
        department_id=u.department_id,
        is_active=u.is_active,
        total_credits=u.total_credits or 0.0,
        created_at=u.created_at or datetime.utcnow(),
        blockchain_tx_hash=blockchain_tx_hash,
    )


def _dept_to_response(d: Department, blockchain_tx_hash: _Opt[str] = None) -> DepartmentResponse:
    return DepartmentResponse(
        id=d.id,
        institution_id=d.institution_id,
        code=d.code,
        name=d.name,
        hod_id=d.hod_id,
        is_active=d.is_active,
        created_at=d.created_at or datetime.utcnow(),
        blockchain_tx_hash=blockchain_tx_hash,
    )


def _get_institution_id(current_user: dict) -> int:
    """Extract institution_id from token — institute admins are always scoped."""
    inst_id = current_user.get("institution_id")
    if not inst_id and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Institute admin account has no institution assigned.",
        )
    return inst_id


# ─── Pending Faculty ───────────────────────────────────────────────────────────

@router.get("/pending", response_model=List[UserResponse])
async def list_pending_faculty(
    current_user: dict = Depends(require_institute_admin),
    db: AsyncSession = Depends(get_db),
):
    """Faculty/HoD pending approval for this institution."""
    institution_id = _get_institution_id(current_user)
    result = await db.execute(
        select(User).where(
            User.institution_id == institution_id,
            User.is_active == False,
            User.role.in_([DBUserRole.FACULTY, DBUserRole.HOD]),
        ).order_by(User.created_at.desc())
    )
    return [_user_to_response(u) for u in result.scalars().all()]


@router.post("/users/{wallet_address}/approve", response_model=UserResponse)
async def approve_faculty(
    wallet_address: str,
    current_user: dict = Depends(require_institute_admin),
    db: AsyncSession = Depends(get_db),
):
    """Approve a pending faculty/HoD registration."""
    institution_id = _get_institution_id(current_user)

    user = (await db.execute(
        select(User).where(User.wallet_address == wallet_address.lower())
    )).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if user.institution_id != institution_id and current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User belongs to a different institution.")
    if user.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already active.")

    user.is_active = True
    await db.commit()
    await db.refresh(user)
    return _user_to_response(user)


@router.post("/users/{wallet_address}/reject")
async def reject_faculty(
    wallet_address: str,
    current_user: dict = Depends(require_institute_admin),
    db: AsyncSession = Depends(get_db),
):
    """Reject (delete) a pending faculty/HoD registration."""
    institution_id = _get_institution_id(current_user)

    user = (await db.execute(
        select(User).where(User.wallet_address == wallet_address.lower())
    )).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if user.institution_id != institution_id and current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User belongs to a different institution.")
    if user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot reject an already active user.")

    await db.delete(user)
    await db.commit()
    return {"message": f"Registration for {wallet_address} rejected and removed."}


# ─── Faculty Management ────────────────────────────────────────────────────────

@router.get("/users", response_model=List[UserResponse])
async def list_institution_users(
    current_user: dict = Depends(require_institute_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all active users in this institution."""
    institution_id = _get_institution_id(current_user)
    result = await db.execute(
        select(User).where(
            User.institution_id == institution_id,
            User.is_active == True,
        ).order_by(User.name)
    )
    return [_user_to_response(u) for u in result.scalars().all()]


@router.post("/users/{wallet_address}/assign-hod")
async def assign_hod(
    wallet_address: str,
    current_user: dict = Depends(require_institute_admin),
    db: AsyncSession = Depends(get_db),
):
    """Promote an active faculty member to HoD for their department."""
    institution_id = _get_institution_id(current_user)

    user = (await db.execute(
        select(User).where(User.wallet_address == wallet_address.lower())
    )).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if user.institution_id != institution_id and current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User belongs to a different institution.")
    if not user.department_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User has no department assigned.")

    dept = await db.get(Department, user.department_id)
    if dept and dept.hod_id and dept.hod_id != user.id:
        old_hod = await db.get(User, dept.hod_id)
        if old_hod:
            old_hod.role = DBUserRole.FACULTY

    user.role = DBUserRole.HOD
    if dept:
        dept.hod_id = user.id

    await db.commit()
    return {"message": f"{user.name} promoted to HoD.", "user_id": user.id}


# ─── Department Management ─────────────────────────────────────────────────────

@router.get("/departments", response_model=List[DepartmentResponse])
async def list_departments(
    current_user: dict = Depends(require_institute_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all departments for this institution."""
    institution_id = _get_institution_id(current_user)
    result = await db.execute(
        select(Department).where(Department.institution_id == institution_id).order_by(Department.name)
    )
    return [_dept_to_response(d) for d in result.scalars().all()]


@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    dept: _DeptCreate,
    current_user: dict = Depends(require_institute_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a department under this institution. institution_id is taken from the JWT."""
    institution_id = _get_institution_id(current_user)

    existing = (await db.execute(
        select(Department).where(
            Department.institution_id == institution_id,
            Department.code == dept.code.upper(),
        )
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Department code already exists in this institution.")

    hod_id = None
    if dept.hod_wallet_address:
        hod = (await db.execute(
            select(User).where(User.wallet_address == dept.hod_wallet_address.lower())
        )).scalar_one_or_none()
        if hod:
            hod_id = hod.id
            hod.role = DBUserRole.HOD

    department = Department(
        institution_id=institution_id,
        code=dept.code.upper(),
        name=dept.name,
        hod_id=hod_id,
        is_active=True,
    )
    db.add(department)
    await db.commit()
    await db.refresh(department)

    if hod_id:
        hod = await db.get(User, hod_id)
        if hod:
            hod.department_id = department.id
        await db.commit()

    blockchain_tx_hash = None
    try:
        if blockchain_service.is_connected and dept.hod_wallet_address:
            tx_result = await blockchain_service.create_department(
                code=dept.code,
                name=dept.name,
                hod_address=dept.hod_wallet_address,
            )
            blockchain_tx_hash = tx_result.get("tx_hash")
    except Exception as e:
        print(f"Blockchain department creation failed: {e}")

    return _dept_to_response(department, blockchain_tx_hash=blockchain_tx_hash)


# ─── Stats ─────────────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_institution_stats(
    current_user: dict = Depends(require_institute_admin),
    db: AsyncSession = Depends(get_db),
):
    """Overview stats for this institution."""
    institution_id = _get_institution_id(current_user)

    total_faculty = (await db.execute(
        select(func.count(User.id)).where(
            User.institution_id == institution_id,
            User.role == DBUserRole.FACULTY,
            User.is_active == True,
        )
    )).scalar() or 0

    total_hod = (await db.execute(
        select(func.count(User.id)).where(
            User.institution_id == institution_id,
            User.role == DBUserRole.HOD,
            User.is_active == True,
        )
    )).scalar() or 0

    pending_count = (await db.execute(
        select(func.count(User.id)).where(
            User.institution_id == institution_id,
            User.is_active == False,
            User.role.in_([DBUserRole.FACULTY, DBUserRole.HOD]),
        )
    )).scalar() or 0

    dept_count = (await db.execute(
        select(func.count(Department.id)).where(Department.institution_id == institution_id)
    )).scalar() or 0

    # Count contributions from faculty in this institution
    faculty_ids_result = await db.execute(
        select(User.id).where(User.institution_id == institution_id)
    )
    faculty_ids = [row[0] for row in faculty_ids_result.fetchall()]
    contrib_count = 0
    if faculty_ids:
        contrib_count = (await db.execute(
            select(func.count(Contribution.id)).where(Contribution.faculty_id.in_(faculty_ids))
        )).scalar() or 0

    inst = await db.get(Institution, institution_id)

    return {
        "institution": {"name": inst.name if inst else None, "id": institution_id},
        "users": {
            "total": total_faculty + total_hod,
            "pending": pending_count,
            "by_role": {"faculty": total_faculty, "hod": total_hod},
        },
        "departments": {"total": dept_count},
        "contributions": {"total": contrib_count},
    }
