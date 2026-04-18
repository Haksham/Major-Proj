"""
SALF Security Module
Authentication and Authorization using MetaMask signatures
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from eth_account.messages import encode_defunct
from web3 import Web3

from app.core.config import settings


# Password hashing context for backup auth
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token
security = HTTPBearer()


def verify_signature(message: str, signature: str, address: str) -> bool:
    """
    Verify an Ethereum signature.
    Used for MetaMask authentication.
    """
    try:
        w3 = Web3()
        message_hash = encode_defunct(text=message)
        recovered_address = w3.eth.account.recover_message(message_hash, signature=signature)
        return recovered_address.lower() == address.lower()
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Get the current authenticated user from JWT token."""
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    
    return {
        "address": payload.get("sub"),
        "role": payload.get("role"),
        "faculty_id": payload.get("faculty_id"),
    }


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def generate_nonce() -> str:
    """Generate a random nonce for MetaMask signing."""
    import secrets
    return secrets.token_hex(16)


def create_sign_message(address: str, nonce: str) -> str:
    """Create the message to be signed by MetaMask."""
    # Keep message deterministic so the same string is signed and later verified.
    return f"SALF Authentication\n\nAddress: {address}\nNonce: {nonce}"


class RoleChecker:
    """Dependency for role-based access control."""
    
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles
    
    async def __call__(self, user: dict = Depends(get_current_user)):
        if user.get("role") not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return user


# Role checker instances
require_faculty = RoleChecker(["faculty", "hod", "admin"])
require_hod = RoleChecker(["hod", "admin"])
require_admin = RoleChecker(["admin"])
