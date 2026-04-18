"""
SALF Pydantic Schemas
Request and Response models for API validation
"""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


# Enums
class UserRole(str, Enum):
    FACULTY = "faculty"
    HOD = "hod"
    ADMIN = "admin"


class ContributionCategory(str, Enum):
    REFEREED_JOURNAL = "refereed_journal"
    INTERNATIONAL_BOOK = "international_book"
    NATIONAL_BOOK = "national_book"
    BOOK_CHAPTER = "book_chapter"
    INTERNATIONAL_LECTURE = "international_lecture"
    NATIONAL_CONFERENCE = "national_conference"
    PATENT_FILED = "patent_filed"
    PATENT_GRANTED = "patent_granted"
    EDITORIAL_WORK = "editorial_work"
    RESEARCH_PROJECT = "research_project"


class ContributionStatus(str, Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    VALIDATED = "validated"
    REJECTED = "rejected"
    FLAGGED = "flagged"


# Authentication Schemas
class NonceRequest(BaseModel):
    """Request for authentication nonce."""
    wallet_address: str = Field(..., pattern=r"^0x[a-fA-F0-9]{40}$")


class NonceResponse(BaseModel):
    """Response with authentication nonce."""
    nonce: str
    message: str


class AuthRequest(BaseModel):
    """Authentication request with signature."""
    wallet_address: str = Field(..., pattern=r"^0x[a-fA-F0-9]{40}$")
    signature: str
    nonce: str


class AuthResponse(BaseModel):
    """Authentication response with tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class RefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


# User Schemas
class UserBase(BaseModel):
    """Base user schema."""
    name: str = Field(..., min_length=2, max_length=255)
    email: Optional[str] = None
    employee_id: Optional[str] = None
    institution: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user."""
    wallet_address: str = Field(..., pattern=r"^0x[a-fA-F0-9]{40}$")
    role: UserRole = UserRole.FACULTY
    department_code: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    name: Optional[str] = None
    email: Optional[str] = None
    employee_id: Optional[str] = None
    institution: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """User response schema."""
    id: int
    wallet_address: str
    role: UserRole
    department_id: Optional[int]
    is_active: bool
    total_credits: float
    created_at: datetime

    class Config:
        from_attributes = True


# Department Schemas
class DepartmentCreate(BaseModel):
    """Schema for creating a department."""
    code: str = Field(..., min_length=2, max_length=20)
    name: str = Field(..., min_length=2, max_length=255)
    hod_wallet_address: Optional[str] = None


class DepartmentResponse(BaseModel):
    """Department response schema."""
    id: int
    code: str
    name: str
    hod_id: Optional[int]
    is_active: bool
    created_at: datetime
    faculty_count: int = 0

    class Config:
        from_attributes = True


# Contribution Schemas
class ContributionMetadata(BaseModel):
    """Metadata for academic contribution."""
    journal_name: Optional[str] = None
    isbn: Optional[str] = None
    issn: Optional[str] = None
    doi: Optional[str] = None
    publication_date: Optional[datetime] = None
    co_authors: Optional[List[str]] = None


class ContributionCreate(BaseModel):
    """Schema for submitting a contribution."""
    category: ContributionCategory
    title: str = Field(..., min_length=5, max_length=500)
    abstract: str = Field(..., min_length=100)
    metadata: Optional[ContributionMetadata] = None


class ContributionResponse(BaseModel):
    """Contribution response schema."""
    id: int
    blockchain_id: Optional[int]
    faculty_id: int
    category: ContributionCategory
    title: str
    abstract: Optional[str]
    ipfs_hash: Optional[str]
    status: ContributionStatus
    ai_quality_score: float
    novelty_percentage: float
    base_credits: float
    final_credits: float
    reviewer_id: Optional[int]
    review_notes: Optional[str]
    submission_time: datetime
    fraud_score: float
    is_flagged: bool
    blockchain_tx_hash: Optional[str]

    class Config:
        from_attributes = True


class ContributionReview(BaseModel):
    """Schema for reviewing a contribution."""
    action: str = Field(..., pattern=r"^(validate|reject|flag)$")
    notes: str = Field(..., min_length=10, max_length=1000)


# AI Evaluation Schemas
class EvaluationRequest(BaseModel):
    """Request for AI evaluation."""
    contribution_id: int
    abstract: str


class EvaluationResponse(BaseModel):
    """AI evaluation response."""
    contribution_id: int
    quality_score: float = Field(..., ge=0, le=100)
    novelty_percentage: float = Field(..., ge=0, le=100)
    benchmark_scores: dict
    fraud_probability: float
    is_flagged: bool
    flag_reasons: Optional[List[str]] = None


# Portfolio Schemas
class PortfolioSummary(BaseModel):
    """Academic credit portfolio summary."""
    total_credits: float
    total_contributions: int
    validated_count: int
    pending_count: int
    rejected_count: int
    flagged_count: int
    contributions_by_category: dict
    credits_by_category: dict


class PortfolioDetail(PortfolioSummary):
    """Detailed portfolio with contributions list."""
    contributions: List[ContributionResponse]
    recent_activity: List[dict]


# Dashboard Schemas
class DashboardStats(BaseModel):
    """Dashboard statistics for admins/HoD."""
    total_faculty: int
    total_contributions: int
    pending_reviews: int
    total_credits_awarded: float
    contributions_this_month: int
    top_contributors: List[dict]
    category_distribution: dict


# Blockchain Schemas
class BlockchainTransaction(BaseModel):
    """Blockchain transaction response."""
    tx_hash: str
    block_number: int
    gas_used: int
    status: str
    timestamp: datetime


class ContractInfo(BaseModel):
    """Smart contract information."""
    name: str
    address: str
    abi_version: str
    deployed_at: Optional[datetime]


# IPFS Schemas
class IPFSUploadResponse(BaseModel):
    """IPFS upload response."""
    cid: str
    size: int
    filename: str
    gateway_url: str


# Error Schemas
class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class ValidationErrorDetail(BaseModel):
    """Validation error detail."""
    loc: List[Any]
    msg: str
    type: str


class ValidationErrorResponse(BaseModel):
    """Validation error response."""
    detail: List[ValidationErrorDetail]


# Pagination
class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# Update forward references
AuthResponse.model_rebuild()
