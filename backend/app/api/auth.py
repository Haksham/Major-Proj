"""
SALF API Routes - Authentication
MetaMask-based authentication with JWT tokens
"""
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as aioredis

from app.schemas.schemas import (
    NonceRequest, NonceResponse, RegisterRequest, InstituteRegisterRequest,
    AuthRequest, AuthResponse, RefreshRequest, UserResponse, UserRole, Designation,
)
from app.core.security import (
    verify_signature, create_access_token, create_refresh_token,
    decode_token, generate_nonce, create_sign_message, get_current_user,
)
from app.core.database import get_db
from app.core.redis_client import get_redis
from app.models.database import User, Department, Institution, UserRole as DBUserRole, Designation as DBDesignation

router = APIRouter(prefix="/auth", tags=["Authentication"])

NONCE_TTL = 300  # seconds

# The seeded admin wallet — can login without pre-registration
_ADMIN_WALLET = "0x3ad3616fe1e978a3fcb1ac52806652c0254d00ba"


def _to_response(u: User) -> UserResponse:
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


# ─── Nonce ────────────────────────────────────────────────────────────────────

@router.post("/nonce", response_model=NonceResponse)
async def get_nonce(
    request: NonceRequest,
    redis: aioredis.Redis = Depends(get_redis),
):
    """
    Step 1 of MetaMask login: request a one-time nonce stored in Redis (5 min TTL).
    The user signs the returned message string with their wallet.
    """
    address = request.wallet_address.lower()
    nonce = generate_nonce()
    message = create_sign_message(address, nonce)
    await redis.setex(f"nonce:{address}", NONCE_TTL, nonce)
    return NonceResponse(nonce=nonce, message=message)


# ─── Register ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Self-service registration — must provide a valid institution_id + department_code.

    Rules:
    - Institution must exist and be active.
    - Department must belong to that institution and be active.
    - role must be 'faculty' or 'hod' (admin is seeded at startup).
    - wallet_address must not already be registered.
    """
    if body.role in (UserRole.ADMIN, UserRole.INSTITUTE_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Use POST /auth/register/institute to register as an institute admin.",
        )

    address = body.wallet_address.lower()

    # Wallet must not be registered yet
    existing = (await db.execute(select(User).where(User.wallet_address == address))).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Wallet address is already registered.",
        )

    # Institution must exist and be active
    institution = (await db.execute(
        select(Institution).where(Institution.id == body.institution_id, Institution.is_active == True)
    )).scalar_one_or_none()
    if not institution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Institution with id={body.institution_id} not found or inactive.",
        )

    # Department must belong to that institution and be active
    department = (await db.execute(
        select(Department).where(
            Department.institution_id == body.institution_id,
            Department.code == body.department_code.upper(),
            Department.is_active == True,
        )
    )).scalar_one_or_none()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department '{body.department_code}' not found in institution {institution.name}.",
        )

    # Create user — inactive until admin approves
    user = User(
        wallet_address=address,
        name=body.name,
        email=body.email,
        employee_id=body.employee_id,
        role=DBUserRole(body.role.value),
        designation=DBDesignation(body.designation.value) if body.designation else None,
        institution_id=body.institution_id,
        department_id=department.id,
        is_active=False,
        total_credits=0.0,
    )
    db.add(user)

    # If registering as HoD and the department has no HoD yet, assign them
    if body.role == UserRole.HOD and department.hod_id is None:
        await db.flush()          # get user.id before committing
        department.hod_id = user.id

    await db.commit()
    await db.refresh(user)
    return _to_response(user)


@router.post("/register/institute", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_institute(
    body: InstituteRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new institution + its admin account.
    Both institution and admin start inactive — pending master-admin approval.
    """
    address = body.wallet_address.lower()

    existing = (await db.execute(select(User).where(User.wallet_address == address))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Wallet address is already registered.")

    existing_inst = (await db.execute(
        select(Institution).where(Institution.code == body.institution_code.upper())
    )).scalar_one_or_none()
    if existing_inst:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Institution code already exists.")

    # Create institution (inactive until master admin approves)
    institution = Institution(
        code=body.institution_code.upper(),
        name=body.institution_name,
        admin_address=body.institution_admin_address or address,
        is_active=False,
    )
    db.add(institution)
    await db.flush()

    # Create institute admin user (also inactive)
    user = User(
        wallet_address=address,
        name=body.name,
        email=body.email,
        role=DBUserRole.INSTITUTE_ADMIN,
        institution_id=institution.id,
        is_active=False,
        total_credits=0.0,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _to_response(user)


# ─── Login ────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=AuthResponse)
async def login(
    request: AuthRequest,
    redis: aioredis.Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
):
    """
    Step 2 of MetaMask login: verify signature, issue JWT tokens.
    The wallet must be pre-registered via POST /auth/register (admin is pre-seeded).
    """
    address = request.wallet_address.lower()

    # Verify nonce
    stored_nonce = await redis.get(f"nonce:{address}")
    if not stored_nonce or stored_nonce != request.nonce:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired nonce. Request a new one via POST /auth/nonce.",
        )

    # Verify Ethereum signature
    message = create_sign_message(address, request.nonce)
    if not verify_signature(message, request.signature, address):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid wallet signature.",
        )

    await redis.delete(f"nonce:{address}")

    # Look up registered user
    result = await db.execute(select(User).where(User.wallet_address == address))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Wallet not registered. "
                "Please register first via POST /api/v1/auth/register with your institution and department."
            ),
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="pending_approval",
        )

    token_data = {
        "sub": address,
        "role": user.role.value,
        "faculty_id": user.id,
        "institution_id": user.institution_id,
    }
    return AuthResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        user=_to_response(user),
    )


# ─── Refresh ──────────────────────────────────────────────────────────────────

@router.post("/refresh", response_model=dict)
async def refresh_token(request: RefreshRequest):
    """Refresh access token using a valid refresh token."""
    payload = decode_token(request.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type.")
    token_data = {
        "sub": payload.get("sub"),
        "role": payload.get("role"),
        "faculty_id": payload.get("faculty_id"),
        "institution_id": payload.get("institution_id"),
    }
    return {"access_token": create_access_token(token_data), "token_type": "bearer"}


# ─── Me ───────────────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the currently authenticated user's profile."""
    result = await db.execute(select(User).where(User.wallet_address == user.get("address")))
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return _to_response(db_user)


@router.post("/logout")
async def logout(user: dict = Depends(get_current_user)):
    """Logout (client must discard tokens)."""
    return {"message": "Successfully logged out."}
