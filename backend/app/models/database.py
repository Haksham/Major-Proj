"""
SALF Database Models
SQLAlchemy ORM models for the application
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, Enum, UniqueConstraint,
)
from sqlalchemy.orm import relationship, declarative_base
import enum


Base = declarative_base()


class UserRole(str, enum.Enum):
    FACULTY = "faculty"
    HOD = "hod"
    INSTITUTE_ADMIN = "institute_admin"
    ADMIN = "admin"


class Designation(str, enum.Enum):
    PROFESSOR = "professor"
    ASSOCIATE_PROFESSOR = "associate_professor"
    ASSISTANT_PROFESSOR = "assistant_professor"
    STAFF = "staff"


class ContributionCategory(str, enum.Enum):
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


class ContributionStatus(str, enum.Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    VALIDATED = "validated"
    REJECTED = "rejected"
    FLAGGED = "flagged"


class Institution(Base):
    """An academic institution. Must exist before any HoD or Faculty can register."""
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    admin_address = Column(String(42))        # deployer / institutional admin wallet
    ledger_contract = Column(String(42))      # on-chain contract address (optional)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    departments = relationship("Department", back_populates="institution")
    users = relationship("User", back_populates="institution")


class Department(Base):
    """Department within an institution. Code is unique per institution."""
    __tablename__ = "departments"
    __table_args__ = (
        UniqueConstraint("institution_id", "code", name="uq_dept_institution_code"),
    )

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False)
    code = Column(String(20), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    hod_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    institution = relationship("Institution", back_populates="departments")
    faculty = relationship("User", back_populates="department", foreign_keys="User.department_id")


class User(Base):
    """User model — Faculty, HoD, or Admin. Must belong to an Institution + Department (except Admin)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    wallet_address = Column(String(42), unique=True, index=True, nullable=False)
    employee_id = Column(String(50), index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), index=True)
    role = Column(Enum(UserRole), default=UserRole.FACULTY)

    # Institution & department membership (required for faculty/hod; null for admin)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    designation = Column(
        Enum(Designation, name="userdesignation", values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    is_active = Column(Boolean, default=True)
    total_credits = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    institution = relationship("Institution", back_populates="users")
    department = relationship("Department", back_populates="faculty", foreign_keys=[department_id])
    contributions = relationship("Contribution", back_populates="faculty", foreign_keys="Contribution.faculty_id")
    reviewed_contributions = relationship("Contribution", back_populates="reviewer", foreign_keys="Contribution.reviewer_id")


class Contribution(Base):
    """Academic contribution submitted by a faculty member."""
    __tablename__ = "contributions"

    id = Column(Integer, primary_key=True, index=True)
    blockchain_id = Column(Integer, index=True)
    faculty_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    faculty_address = Column(String(42), index=True)   # denormalised for fast ownership checks
    category = Column(Enum(ContributionCategory), nullable=False)
    title = Column(String(500), nullable=False)
    abstract = Column(Text)
    ipfs_hash = Column(String(100), unique=True, index=True)
    metadata_hash = Column(String(100), unique=True, index=True)
    file_name = Column(String(255))
    file_size = Column(Integer)

    # Publication metadata
    journal_name = Column(String(255))
    isbn = Column(String(20))
    issn = Column(String(20))
    doi = Column(String(100))
    publication_date = Column(DateTime)
    co_authors = Column(Text)

    # Status and AI scoring
    status = Column(Enum(ContributionStatus), default=ContributionStatus.PENDING)
    ai_quality_score = Column(Float, default=0.0)
    novelty_percentage = Column(Float, default=0.0)
    base_credits = Column(Float, default=0.0)
    final_credits = Column(Float, default=0.0)
    calculated_credits = Column(Float, default=0.0)    # pre-validation AI estimate
    evaluation_details = Column(Text)                  # JSON from REM

    # Review
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_notes = Column(Text)
    review_time = Column(DateTime)

    # Fraud detection
    fraud_score = Column(Float, default=0.0)
    is_flagged = Column(Boolean, default=False)
    flag_reason = Column(Text)
    fraud_reasons = Column(Text)                       # JSON list

    # Timestamps
    submission_time = Column(DateTime, default=datetime.utcnow)
    blockchain_tx_hash = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    faculty = relationship("User", back_populates="contributions", foreign_keys=[faculty_id])
    reviewer = relationship("User", back_populates="reviewed_contributions", foreign_keys=[reviewer_id])


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(Integer)
    details = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    timestamp = Column(DateTime, default=datetime.utcnow)
    blockchain_tx_hash = Column(String(100))


class BenchmarkAttribute(Base):
    __tablename__ = "benchmark_attributes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    weight = Column(Float, default=1.0)
    category = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
