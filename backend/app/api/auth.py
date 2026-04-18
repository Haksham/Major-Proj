"""
SALF API Routes - Authentication
MetaMask-based authentication with JWT tokens
"""
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.schemas import (
    NonceRequest, NonceResponse, AuthRequest, AuthResponse,
    RefreshRequest, UserResponse
)
from app.core.security import (
    verify_signature, create_access_token, create_refresh_token,
    decode_token, generate_nonce, create_sign_message, get_current_user
)
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

# In-memory nonce storage (use Redis in production)
_nonces: dict = {}

# Mock user database (replace with actual database in production)
_users: dict = {
    "0xfe3b557e8fb62b89f4916b721be55ceb828dbd73": {
        "id": 1,
        "wallet_address": "0xfe3b557e8fb62b89f4916b721be55ceb828dbd73",
        "name": "Admin User",
        "email": "admin@salf.edu",
        "role": "admin",
        "department_id": None,
        "is_active": True,
        "total_credits": 0,
        "employee_id": "ADMIN001",
        "institution": "SALF University"
    }
}


@router.post("/nonce", response_model=NonceResponse)
async def get_nonce(request: NonceRequest):
    """
    Get a nonce for MetaMask signing.
    
    The user must sign this message with their wallet to authenticate.
    """
    address = request.wallet_address.lower()
    nonce = generate_nonce()
    message = create_sign_message(address, nonce)
    
    # Store nonce (use Redis with TTL in production)
    _nonces[address] = nonce
    
    return NonceResponse(nonce=nonce, message=message)


@router.post("/login", response_model=AuthResponse)
async def login(request: AuthRequest):
    """
    Authenticate using MetaMask signature.
    
    1. User requests a nonce
    2. User signs the message with MetaMask
    3. Backend verifies signature and issues JWT tokens
    """
    address = request.wallet_address.lower()
    
    # Verify nonce exists
    stored_nonce = _nonces.get(address)
    if not stored_nonce or stored_nonce != request.nonce:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired nonce"
        )
    
    # Create the message that was signed
    message = create_sign_message(address, request.nonce)
    
    # Verify signature
    if not verify_signature(message, request.signature, address):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )
    
    # Clear used nonce
    del _nonces[address]
    
    # Get or create user
    user = _users.get(address)
    if not user:
        # Auto-register new users as faculty
        user = {
            "id": len(_users) + 1,
            "wallet_address": address,
            "name": f"Faculty_{address[:8]}",
            "email": None,
            "role": "faculty",
            "department_id": None,
            "is_active": True,
            "total_credits": 0,
            "employee_id": None,
            "institution": None
        }
        _users[address] = user
    
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Create tokens
    token_data = {
        "sub": address,
        "role": user["role"],
        "faculty_id": user["id"]
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(
            id=user["id"],
            wallet_address=user["wallet_address"],
            name=user["name"],
            email=user.get("email"),
            employee_id=user.get("employee_id"),
            institution=user.get("institution"),
            role=user["role"],
            department_id=user.get("department_id"),
            is_active=user["is_active"],
            total_credits=user["total_credits"],
            created_at=datetime.utcnow()  # placeholder until DB-backed
        )
    )


@router.post("/refresh", response_model=dict)
async def refresh_token(request: RefreshRequest):
    """
    Refresh access token using refresh token.
    """
    payload = decode_token(request.refresh_token)
    
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    # Create new access token
    token_data = {
        "sub": payload.get("sub"),
        "role": payload.get("role"),
        "faculty_id": payload.get("faculty_id")
    }
    
    new_access_token = create_access_token(token_data)
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information.
    """
    address = user.get("address")
    user_data = _users.get(address)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user_data["id"],
        wallet_address=user_data["wallet_address"],
        name=user_data["name"],
        email=user_data.get("email"),
        employee_id=user_data.get("employee_id"),
        institution=user_data.get("institution"),
        role=user_data["role"],
        department_id=user_data.get("department_id"),
        is_active=user_data["is_active"],
        total_credits=user_data["total_credits"],
        created_at=None
    )


@router.post("/logout")
async def logout(user: dict = Depends(get_current_user)):
    """
    Logout user.
    
    In a production system, this would invalidate the refresh token.
    """
    return {"message": "Successfully logged out"}
