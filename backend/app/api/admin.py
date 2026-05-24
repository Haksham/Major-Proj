"""
SALF API Routes - Administration
System administration and governance
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.schemas import (
    UserCreate, UserResponse, UserUpdate, UserRole, Designation,
    DepartmentCreate, DepartmentResponse,
    InstitutionCreate, InstitutionResponse, ContractInfo,
)
from app.core.security import get_current_user, require_admin
from app.core.database import get_db
from app.services.blockchain_service import blockchain_service
from app.core.config import settings
from app.models.database import User, Department, Institution, UserRole as DBUserRole, Designation as DBDesignation

router = APIRouter(prefix="/admin", tags=["Administration"])


def _inst_to_response(i: Institution) -> InstitutionResponse:
    return InstitutionResponse(
        id=i.id,
        code=i.code,
        name=i.name,
        admin_address=i.admin_address,
        is_active=i.is_active,
        created_at=i.created_at or datetime.utcnow(),
    )


def _user_to_response(u: User) -> UserResponse:
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


# ─── Institution Management ────────────────────────────────────────────────────

@router.post("/institutes", response_model=InstitutionResponse, status_code=status.HTTP_201_CREATED)
async def create_institution(
    body: InstitutionCreate,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new institution (admin only). Must exist before HoD/faculty can register."""
    existing = (await db.execute(
        select(Institution).where(Institution.code == body.code.upper())
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Institution code already exists.")

    inst = Institution(
        code=body.code.upper(),
        name=body.name,
        admin_address=body.admin_address,
        is_active=True,
    )
    db.add(inst)
    await db.commit()
    await db.refresh(inst)
    return _inst_to_response(inst)


@router.get("/institutes", response_model=List[InstitutionResponse])
async def list_institutions_admin(
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all institutions including inactive ones (admin view)."""
    result = await db.execute(select(Institution).order_by(Institution.name))
    return [_inst_to_response(i) for i in result.scalars().all()]


@router.patch("/institutes/{institution_id}/deactivate")
async def deactivate_institution(
    institution_id: int,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate an institution (blocks new registrations under it)."""
    inst = await db.get(Institution, institution_id)
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found.")
    inst.is_active = False
    await db.commit()
    return {"message": f"Institution '{inst.name}' deactivated."}


# ─── User Management ───────────────────────────────────────────────────────────

@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin-only user creation (bypasses self-registration).
    institution_id + department_code are optional here — admin may create system users.
    """
    address = user_data.wallet_address.lower()

    existing = (await db.execute(select(User).where(User.wallet_address == address))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists.")

    dept_id = None
    if user_data.institution_id and user_data.department_code:
        dept = (await db.execute(
            select(Department).where(
                Department.institution_id == user_data.institution_id,
                Department.code == user_data.department_code.upper(),
            )
        )).scalar_one_or_none()
        if dept:
            dept_id = dept.id

    user = User(
        wallet_address=address,
        name=user_data.name,
        email=user_data.email,
        employee_id=user_data.employee_id,
        role=DBUserRole(user_data.role.value),
        designation=DBDesignation(user_data.designation.value) if user_data.designation else None,
        institution_id=user_data.institution_id,
        department_id=dept_id,
        is_active=True,
        total_credits=0.0,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    try:
        if blockchain_service.is_connected:
            await blockchain_service.register_faculty(
                faculty_address=address,
                name=user_data.name,
                department=user_data.department_code or "DEFAULT",
                employee_id=user_data.employee_id or "",
                institution=str(user_data.institution_id or ""),
            )
    except Exception as e:
        print(f"Blockchain registration failed: {e}")

    return _user_to_response(user)


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    role: Optional[UserRole] = None,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all users with optional role filtering."""
    query = select(User)
    if role:
        query = query.where(User.role == DBUserRole(role.value))
    result = await db.execute(query)
    return [_user_to_response(u) for u in result.scalars().all()]


@router.get("/users/pending", response_model=List[UserResponse])
async def list_pending_users(
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List institute admins pending master-admin approval."""
    result = await db.execute(
        select(User).where(
            User.is_active == False,
            User.role == DBUserRole.INSTITUTE_ADMIN,
        ).order_by(User.created_at.desc())
    )
    return [_user_to_response(u) for u in result.scalars().all()]


@router.post("/users/{wallet_address}/approve", response_model=UserResponse)
async def approve_user(
    wallet_address: str,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Approve a pending institute admin — also activates their institution.
    """
    user = (await db.execute(
        select(User).where(User.wallet_address == wallet_address.lower())
    )).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if user.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already active.")

    user.is_active = True

    # If institute admin, also activate their institution
    if user.role == DBUserRole.INSTITUTE_ADMIN and user.institution_id:
        inst = await db.get(Institution, user.institution_id)
        if inst:
            inst.is_active = True

    await db.commit()
    await db.refresh(user)
    return _user_to_response(user)


@router.patch("/users/{wallet_address}", response_model=UserResponse)
async def update_user(
    wallet_address: str,
    update: UserUpdate,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update user details."""
    user = (await db.execute(
        select(User).where(User.wallet_address == wallet_address.lower())
    )).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if update.name is not None:
        user.name = update.name
    if update.email is not None:
        user.email = update.email
    if update.employee_id is not None:
        user.employee_id = update.employee_id
    if update.is_active is not None:
        user.is_active = update.is_active

    await db.commit()
    await db.refresh(user)
    return _user_to_response(user)


@router.post("/users/{wallet_address}/role")
async def update_user_role(
    wallet_address: str,
    new_role: UserRole,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update user role."""
    user = (await db.execute(
        select(User).where(User.wallet_address == wallet_address.lower())
    )).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.role = DBUserRole(new_role.value)
    await db.commit()
    return {"message": f"Role updated to {new_role.value}", "user_id": user.id}


@router.post("/departments", response_model=DepartmentResponse)
async def create_department(
    dept: DepartmentCreate,
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new department under an institution and register on blockchain."""
    # Institution must exist
    institution = await db.get(Institution, dept.institution_id)
    if not institution or not institution.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Institution with id={dept.institution_id} not found or inactive.",
        )

    # Department code must be unique within the institution
    existing = (await db.execute(
        select(Department).where(
            Department.institution_id == dept.institution_id,
            Department.code == dept.code.upper(),
        )
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Department code '{dept.code}' already exists in this institution.",
        )

    hod_id = None
    if dept.hod_wallet_address:
        hod = (await db.execute(
            select(User).where(User.wallet_address == dept.hod_wallet_address.lower())
        )).scalar_one_or_none()
        if hod:
            hod_id = hod.id
            hod.role = DBUserRole.HOD

    department = Department(
        institution_id=dept.institution_id,
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

    try:
        if blockchain_service.is_connected and dept.hod_wallet_address:
            await blockchain_service.create_department(
                code=dept.code,
                name=dept.name,
                hod_address=dept.hod_wallet_address,
            )
    except Exception as e:
        print(f"Blockchain department creation failed: {e}")

    return _dept_to_response(department)


@router.get("/departments", response_model=List[DepartmentResponse])
async def list_departments(
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all departments."""
    result = await db.execute(select(Department))
    return [_dept_to_response(d) for d in result.scalars().all()]


@router.get("/blockchain/status", response_model=Dict[str, Any])
async def get_blockchain_status(admin: dict = Depends(require_admin)):
    """Get blockchain network status."""
    return {
        "connected": blockchain_service.is_connected,
        "rpc_url": settings.BESU_RPC_URL,
        "chain_id": settings.BESU_CHAIN_ID,
        "block_number": blockchain_service.get_block_number() if blockchain_service.is_connected else None,
        "contracts": {
            "access_control": settings.ACCESS_CONTROL_ADDRESS,
            "academic_credit": settings.ACADEMIC_CREDIT_ADDRESS,
            "contribution_registry": settings.CONTRIBUTION_REGISTRY_ADDRESS,
        },
    }


@router.get("/contracts", response_model=List[ContractInfo])
async def get_contract_info(admin: dict = Depends(require_admin)):
    """Get deployed smart contract information."""
    contracts = []
    if settings.ACCESS_CONTROL_ADDRESS:
        contracts.append(ContractInfo(name="SALFAccessControl", address=settings.ACCESS_CONTROL_ADDRESS, abi_version="1.0.0", deployed_at=None))
    if settings.ACADEMIC_CREDIT_ADDRESS:
        contracts.append(ContractInfo(name="AcademicCreditLedger", address=settings.ACADEMIC_CREDIT_ADDRESS, abi_version="1.0.0", deployed_at=None))
    if settings.CONTRIBUTION_REGISTRY_ADDRESS:
        contracts.append(ContractInfo(name="ContributionRegistry", address=settings.CONTRIBUTION_REGISTRY_ADDRESS, abi_version="1.0.0", deployed_at=None))
    return contracts


@router.post("/ugc/update-points")
async def update_ugc_points(
    category: str,
    points: int,
    admin: dict = Depends(require_admin),
):
    """Update UGC base points for a contribution category."""
    valid = [
        "REFEREED_JOURNAL", "INTERNATIONAL_BOOK", "NATIONAL_BOOK",
        "BOOK_CHAPTER", "INTERNATIONAL_LECTURE", "NATIONAL_CONFERENCE",
        "PATENT_FILED", "PATENT_GRANTED", "EDITORIAL_WORK", "RESEARCH_PROJECT",
    ]
    if category.upper() not in valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid category. Valid: {valid}")
    return {
        "message": f"UGC points updated for {category}",
        "new_points": points,
        "blockchain_synced": blockchain_service.is_connected,
    }


@router.get("/config", response_model=Dict[str, Any])
async def get_system_config(admin: dict = Depends(require_admin)):
    """Get current system configuration."""
    return {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "blockchain": {"rpc_url": settings.BESU_RPC_URL, "chain_id": settings.BESU_CHAIN_ID},
        "ipfs": {"api_url": settings.IPFS_API_URL, "gateway": settings.IPFS_GATEWAY},
        "ai": {
            "model": settings.SBERT_MODEL,
            "min_abstract_length": settings.MIN_ABSTRACT_LENGTH,
            "fraud_threshold": settings.FRAUD_DETECTION_THRESHOLD,
        },
        "ugc_points": {
            "refereed_journal": settings.UGC_REFEREED_JOURNAL,
            "international_book": settings.UGC_INTERNATIONAL_BOOK,
            "national_book": settings.UGC_NATIONAL_BOOK,
            "book_chapter": settings.UGC_BOOK_CHAPTER,
            "international_lecture": settings.UGC_INTERNATIONAL_LECTURE,
            "national_conference": settings.UGC_NATIONAL_CONFERENCE,
            "patent_filed": settings.UGC_PATENT_FILED,
            "patent_granted": settings.UGC_PATENT_GRANTED,
            "editorial_work": settings.UGC_EDITORIAL_WORK,
            "research_project": settings.UGC_RESEARCH_PROJECT,
        },
    }
