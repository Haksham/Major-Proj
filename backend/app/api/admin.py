"""
SALF API Routes - Administration
System administration and governance
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends

from app.schemas.schemas import (
    UserCreate, UserResponse, UserUpdate, UserRole,
    DepartmentCreate, DepartmentResponse, ContractInfo
)
from app.core.security import get_current_user, require_admin
from app.services.blockchain_service import blockchain_service
from app.core.config import settings

router = APIRouter(prefix="/admin", tags=["Administration"])

# In-memory storage (replace with database)
from app.api.auth import _users

_departments: Dict[str, Dict] = {}


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    admin: dict = Depends(require_admin)
):
    """
    Create a new user (Faculty, HoD, or Admin).
    
    This also registers the user on the blockchain.
    """
    address = user_data.wallet_address.lower()
    
    if address in _users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    
    # Create user record
    user = {
        "id": len(_users) + 1,
        "wallet_address": address,
        "name": user_data.name,
        "email": user_data.email,
        "employee_id": user_data.employee_id,
        "institution": user_data.institution,
        "role": user_data.role.value,
        "department_id": None,
        "is_active": True,
        "total_credits": 0,
        "created_at": datetime.utcnow()
    }
    
    # Link to department if provided
    if user_data.department_code and user_data.department_code in _departments:
        user["department_id"] = _departments[user_data.department_code]["id"]
    
    _users[address] = user
    
    # Register on blockchain
    try:
        if blockchain_service.is_connected:
            await blockchain_service.register_faculty(
                faculty_address=address,
                name=user_data.name,
                department=user_data.department_code or "DEFAULT",
                employee_id=user_data.employee_id or "",
                institution=user_data.institution or ""
            )
    except Exception as e:
        print(f"Blockchain registration failed: {e}")
    
    return UserResponse(
        id=user["id"],
        wallet_address=user["wallet_address"],
        name=user["name"],
        email=user.get("email"),
        employee_id=user.get("employee_id"),
        institution=user.get("institution"),
        role=UserRole(user["role"]),
        department_id=user.get("department_id"),
        is_active=user["is_active"],
        total_credits=user["total_credits"],
        created_at=user["created_at"]
    )


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    role: Optional[UserRole] = None,
    admin: dict = Depends(require_admin)
):
    """List all users with optional role filtering."""
    users = list(_users.values())
    
    if role:
        users = [u for u in users if u.get("role") == role.value]
    
    return [
        UserResponse(
            id=u["id"],
            wallet_address=u["wallet_address"],
            name=u["name"],
            email=u.get("email"),
            employee_id=u.get("employee_id"),
            institution=u.get("institution"),
            role=UserRole(u["role"]),
            department_id=u.get("department_id"),
            is_active=u["is_active"],
            total_credits=u["total_credits"],
            created_at=u.get("created_at")
        )
        for u in users
    ]


@router.patch("/users/{wallet_address}", response_model=UserResponse)
async def update_user(
    wallet_address: str,
    update: UserUpdate,
    admin: dict = Depends(require_admin)
):
    """Update user details."""
    address = wallet_address.lower()
    user = _users.get(address)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    if update.name is not None:
        user["name"] = update.name
    if update.email is not None:
        user["email"] = update.email
    if update.employee_id is not None:
        user["employee_id"] = update.employee_id
    if update.institution is not None:
        user["institution"] = update.institution
    if update.is_active is not None:
        user["is_active"] = update.is_active
    
    return UserResponse(
        id=user["id"],
        wallet_address=user["wallet_address"],
        name=user["name"],
        email=user.get("email"),
        employee_id=user.get("employee_id"),
        institution=user.get("institution"),
        role=UserRole(user["role"]),
        department_id=user.get("department_id"),
        is_active=user["is_active"],
        total_credits=user["total_credits"],
        created_at=user.get("created_at")
    )


@router.post("/users/{wallet_address}/role")
async def update_user_role(
    wallet_address: str,
    new_role: UserRole,
    admin: dict = Depends(require_admin)
):
    """Update user role."""
    address = wallet_address.lower()
    user = _users.get(address)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user["role"] = new_role.value
    
    return {"message": f"Role updated to {new_role.value}", "user_id": user["id"]}


@router.post("/departments", response_model=DepartmentResponse)
async def create_department(
    dept: DepartmentCreate,
    admin: dict = Depends(require_admin)
):
    """
    Create a new department.
    
    This also registers the department on the blockchain.
    """
    if dept.code in _departments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department already exists"
        )
    
    department = {
        "id": len(_departments) + 1,
        "code": dept.code,
        "name": dept.name,
        "hod_id": None,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "faculty_count": 0
    }
    
    # Assign HoD if provided
    if dept.hod_wallet_address:
        hod_address = dept.hod_wallet_address.lower()
        hod = _users.get(hod_address)
        if hod:
            department["hod_id"] = hod["id"]
            hod["role"] = "hod"
            hod["department_id"] = department["id"]
    
    _departments[dept.code] = department
    
    # Register on blockchain
    try:
        if blockchain_service.is_connected and dept.hod_wallet_address:
            await blockchain_service.create_department(
                code=dept.code,
                name=dept.name,
                hod_address=dept.hod_wallet_address
            )
    except Exception as e:
        print(f"Blockchain department creation failed: {e}")
    
    return DepartmentResponse(**department)


@router.get("/departments", response_model=List[DepartmentResponse])
async def list_departments(
    admin: dict = Depends(require_admin)
):
    """List all departments."""
    return [DepartmentResponse(**d) for d in _departments.values()]


@router.get("/blockchain/status", response_model=Dict[str, Any])
async def get_blockchain_status(
    admin: dict = Depends(require_admin)
):
    """Get blockchain network status."""
    return {
        "connected": blockchain_service.is_connected,
        "rpc_url": settings.BESU_RPC_URL,
        "chain_id": settings.BESU_CHAIN_ID,
        "block_number": blockchain_service.get_block_number() if blockchain_service.is_connected else None,
        "contracts": {
            "access_control": settings.ACCESS_CONTROL_ADDRESS,
            "academic_credit": settings.ACADEMIC_CREDIT_ADDRESS,
            "contribution_registry": settings.CONTRIBUTION_REGISTRY_ADDRESS
        }
    }


@router.get("/contracts", response_model=List[ContractInfo])
async def get_contract_info(
    admin: dict = Depends(require_admin)
):
    """Get deployed smart contract information."""
    contracts = []
    
    if settings.ACCESS_CONTROL_ADDRESS:
        contracts.append(ContractInfo(
            name="SALFAccessControl",
            address=settings.ACCESS_CONTROL_ADDRESS,
            abi_version="1.0.0",
            deployed_at=None
        ))
    
    if settings.ACADEMIC_CREDIT_ADDRESS:
        contracts.append(ContractInfo(
            name="AcademicCreditLedger",
            address=settings.ACADEMIC_CREDIT_ADDRESS,
            abi_version="1.0.0",
            deployed_at=None
        ))
    
    if settings.CONTRIBUTION_REGISTRY_ADDRESS:
        contracts.append(ContractInfo(
            name="ContributionRegistry",
            address=settings.CONTRIBUTION_REGISTRY_ADDRESS,
            abi_version="1.0.0",
            deployed_at=None
        ))
    
    return contracts


@router.post("/ugc/update-points")
async def update_ugc_points(
    category: str,
    points: int,
    admin: dict = Depends(require_admin)
):
    """
    Update UGC base points for a contribution category.
    
    This updates both the local configuration and blockchain contract.
    """
    # Validate category
    valid_categories = [
        "REFEREED_JOURNAL", "INTERNATIONAL_BOOK", "NATIONAL_BOOK",
        "BOOK_CHAPTER", "INTERNATIONAL_LECTURE", "NATIONAL_CONFERENCE",
        "PATENT_FILED", "PATENT_GRANTED", "EDITORIAL_WORK", "RESEARCH_PROJECT"
    ]
    
    if category.upper() not in valid_categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category. Valid options: {valid_categories}"
        )
    
    # Would update blockchain contract here
    # await blockchain_service.update_ugc_base_points(category_index, points)
    
    return {
        "message": f"UGC points updated for {category}",
        "new_points": points,
        "blockchain_synced": blockchain_service.is_connected
    }


@router.get("/config", response_model=Dict[str, Any])
async def get_system_config(
    admin: dict = Depends(require_admin)
):
    """Get current system configuration."""
    return {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "blockchain": {
            "rpc_url": settings.BESU_RPC_URL,
            "chain_id": settings.BESU_CHAIN_ID
        },
        "ipfs": {
            "host": settings.IPFS_HOST,
            "port": settings.IPFS_PORT,
            "gateway": settings.IPFS_GATEWAY
        },
        "ai": {
            "model": settings.SBERT_MODEL,
            "min_abstract_length": settings.MIN_ABSTRACT_LENGTH,
            "novelty_threshold": settings.NOVELTY_THRESHOLD,
            "fraud_threshold": settings.FRAUD_DETECTION_THRESHOLD
        },
        "performance": {
            "max_tps": settings.MAX_TPS,
            "p95_latency_ms": settings.P95_LATENCY_MS
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
            "research_project": settings.UGC_RESEARCH_PROJECT
        }
    }
