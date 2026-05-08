"""
SALF API Routes - Contributions
Academic contribution management endpoints
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form, BackgroundTasks
import hashlib
from fastapi.responses import Response

from app.schemas.schemas import (
    ContributionCreate, ContributionResponse, ContributionReview,
    ContributionCategory, ContributionStatus, EvaluationResponse,
    PortfolioSummary, PortfolioDetail, PaginatedResponse
)
from app.core.security import get_current_user, require_faculty, require_hod
from app.services.ipfs_service import ipfs_service
from app.services.evaluation_service import rem_service
from app.services.fraud_detection import fraud_gatekeeper
from app.services.blockchain_service import blockchain_service
from app.core.config import settings

router = APIRouter(prefix="/contributions", tags=["Contributions"])

# In-memory storage (replace with database in production)
_contributions: dict = {}
_contribution_counter = 0

# UGC base points mapping
UGC_POINTS = {
    ContributionCategory.REFEREED_JOURNAL: settings.UGC_REFEREED_JOURNAL,
    ContributionCategory.INTERNATIONAL_BOOK: settings.UGC_INTERNATIONAL_BOOK,
    ContributionCategory.NATIONAL_BOOK: settings.UGC_NATIONAL_BOOK,
    ContributionCategory.BOOK_CHAPTER: settings.UGC_BOOK_CHAPTER,
    ContributionCategory.INTERNATIONAL_LECTURE: settings.UGC_INTERNATIONAL_LECTURE,
    ContributionCategory.NATIONAL_CONFERENCE: settings.UGC_NATIONAL_CONFERENCE,
    ContributionCategory.PATENT_FILED: settings.UGC_PATENT_FILED,
    ContributionCategory.PATENT_GRANTED: settings.UGC_PATENT_GRANTED,
    ContributionCategory.EDITORIAL_WORK: settings.UGC_EDITORIAL_WORK,
    ContributionCategory.RESEARCH_PROJECT: settings.UGC_RESEARCH_PROJECT,
}

async def _run_ai_evaluation(contribution_id: int) -> None:
    """
    Run REM evaluation and store results on the in-memory contribution.
    Keeps submission fast by moving model load/embedding work off the request path.
    """
    contribution = _contributions.get(contribution_id)
    if not contribution:
        return

    try:
        evaluation = rem_service.evaluate_abstract(contribution["abstract"])
        quality_score = evaluation.get("quality_score", 0) or 0
        novelty_percentage = evaluation.get("novelty_percentage", 0) or 0

        base_credits = contribution.get("base_credits") or UGC_POINTS.get(contribution["category"], 0)
        calculated_credits = rem_service.calculate_final_credits(
            base_credits, quality_score, novelty_percentage
        )

        contribution["ai_quality_score"] = quality_score
        contribution["novelty_percentage"] = novelty_percentage
        contribution["base_credits"] = base_credits
        contribution["calculated_credits"] = calculated_credits
        contribution["evaluation_details"] = {
            "benchmark_scores": evaluation.get("benchmark_scores", {}),
            "keywords_found": evaluation.get("keywords_found", []),
            "abstract_length": evaluation.get("abstract_length"),
            "evaluation_version": evaluation.get("evaluation_version"),
        }
        contribution.pop("evaluation_error", None)
    except Exception as e:
        # Don't fail the submission; store error for debugging.
        contribution["evaluation_error"] = str(e)


@router.get("/ipfs/{cid}")
async def get_ipfs_file(
    cid: str,
    user: dict = Depends(require_faculty),
):
    """
    Retrieve a contribution file by CID via the configured IPFS service.
    Works in both real-IPFS and mock-IPFS modes.
    """
    try:
        content = await ipfs_service.get_file(cid)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CID not found")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to retrieve from IPFS: {str(e)}",
        )

    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{cid}.pdf"'},
    )


@router.post("/submit", response_model=ContributionResponse)
async def submit_contribution(
    background_tasks: BackgroundTasks,
    category: ContributionCategory = Form(...),
    title: str = Form(...),
    abstract: str = Form(...),
    journal_name: Optional[str] = Form(None),
    isbn: Optional[str] = Form(None),
    issn: Optional[str] = Form(None),
    doi: Optional[str] = Form(None),
    co_authors: Optional[str] = Form(None),
    file: UploadFile = File(...),
    user: dict = Depends(require_faculty)
):
    """
    Submit a new academic contribution (UC-01).
    
    1. Upload document to IPFS
    2. Run fraud detection
    3. Run AI evaluation (REM)
    4. Record on blockchain
    5. Return contribution details
    """
    global _contribution_counter
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    # Check file size
    if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum of {settings.MAX_FILE_SIZE_MB}MB"
        )
    
    # Validate abstract length
    if len(abstract) < settings.MIN_ABSTRACT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Abstract must be at least {settings.MIN_ABSTRACT_LENGTH} characters"
        )
    
    # Prepare metadata
    metadata = {
        "journal_name": journal_name,
        "isbn": isbn,
        "issn": issn,
        "doi": doi,
        "co_authors": co_authors.split(",") if co_authors else []
    }
    
    # Step 1: Fraud Detection (Gatekeeper)
    fraud_result = fraud_gatekeeper.detect_fraud(
        faculty_address=user["address"],
        category=category.value,
        title=title,
        abstract=abstract,
        metadata=metadata
    )
    
    if fraud_result["is_flagged"] and fraud_result["fraud_probability"] >= 0.9:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Submission blocked by fraud detection. Contact administrator.",
            headers={"X-Fraud-Reasons": str(fraud_result["flag_reasons"])}
        )
    
    # Step 2: Upload to IPFS
    try:
        ipfs_result = await ipfs_service.upload_file(file_content, file.filename)
        ipfs_hash = ipfs_result["cid"]
        metadata_hash = ipfs_result["metadata_hash"]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload to IPFS: {str(e)}"
        )
    # Step 3: AI Evaluation (REM)
    # Run asynchronously to avoid long request times (model load + embeddings).
    base_credits = UGC_POINTS.get(category, 0)
    
    # Step 4: Create contribution record
    _contribution_counter += 1
    contribution_id = _contribution_counter
    
    contribution = {
        "id": contribution_id,
        "blockchain_id": None,
        "faculty_id": user["faculty_id"],
        "faculty_address": user["address"],
        "category": category,
        "title": title,
        "abstract": abstract,
        "ipfs_hash": ipfs_hash,
        "metadata_hash": metadata_hash,
        "file_name": file.filename,
        "file_size": file_size,
        "journal_name": journal_name,
        "isbn": isbn,
        "issn": issn,
        "doi": doi,
        "co_authors": co_authors,
        "status": ContributionStatus.FLAGGED if fraud_result["is_flagged"] else ContributionStatus.PENDING,
        "ai_quality_score": 0,
        "novelty_percentage": 0,
        "base_credits": base_credits,
        "final_credits": 0,  # Set after validation
        "calculated_credits": 0,  # Filled by background AI evaluation
        "reviewer_id": None,
        "review_notes": None,
        "review_time": None,
        "fraud_score": fraud_result["fraud_probability"],
        "fraud_reasons": fraud_result["flag_reasons"],
        "is_flagged": fraud_result["is_flagged"],
        "flag_reason": ", ".join(fraud_result["flag_reasons"]) if fraud_result["is_flagged"] else None,
        "submission_time": datetime.utcnow(),
        "blockchain_tx_hash": None,
        "created_at": datetime.utcnow()
    }
    
    _contributions[contribution_id] = contribution

    # Kick off AI evaluation in background
    background_tasks.add_task(_run_ai_evaluation, contribution_id)
    
    # Step 5: Submit to blockchain (async)
    try:
        if blockchain_service.is_connected:
            # Map category to enum value
            category_index = list(ContributionCategory).index(category)
            
            tx_result = await blockchain_service.submit_record(
                category=category_index,
                title=title,
                ipfs_hash=ipfs_hash,
                metadata_hash=metadata_hash
            )
            
            contribution["blockchain_id"] = tx_result.get("contribution_id")
            contribution["blockchain_tx_hash"] = tx_result.get("tx_hash")
    except Exception as e:
        # Log but don't fail - blockchain submission can be retried
        print(f"Blockchain submission failed: {e}")
    
    return ContributionResponse(
        id=contribution["id"],
        blockchain_id=contribution["blockchain_id"],
        faculty_id=contribution["faculty_id"],
        category=contribution["category"],
        title=contribution["title"],
        abstract=contribution["abstract"],
        ipfs_hash=contribution["ipfs_hash"],
        status=contribution["status"],
        ai_quality_score=contribution["ai_quality_score"],
        novelty_percentage=contribution["novelty_percentage"],
        base_credits=contribution["base_credits"],
        final_credits=contribution["final_credits"],
        reviewer_id=contribution["reviewer_id"],
        review_notes=contribution["review_notes"],
        submission_time=contribution["submission_time"],
        fraud_score=contribution["fraud_score"],
        is_flagged=contribution["is_flagged"],
        blockchain_tx_hash=contribution["blockchain_tx_hash"]
    )


@router.get("/{contribution_id}", response_model=ContributionResponse)
async def get_contribution(
    contribution_id: int,
    user: dict = Depends(get_current_user)
):
    """Get contribution details by ID."""
    contribution = _contributions.get(contribution_id)
    
    if not contribution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contribution not found"
        )
    
    # Check access permissions
    if user["role"] == "faculty" and contribution["faculty_address"] != user["address"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return ContributionResponse(**contribution)


@router.get("/", response_model=List[ContributionResponse])
async def list_contributions(
    status: Optional[ContributionStatus] = None,
    category: Optional[ContributionCategory] = None,
    page: int = 1,
    page_size: int = 20,
    user: dict = Depends(get_current_user)
):
    """List contributions with optional filtering."""
    # Filter contributions based on role
    if user["role"] == "faculty":
        filtered = [c for c in _contributions.values() if c["faculty_address"] == user["address"]]
    else:
        filtered = list(_contributions.values())
    
    # Apply filters
    if status:
        filtered = [c for c in filtered if c["status"] == status]
    if category:
        filtered = [c for c in filtered if c["category"] == category]
    
    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    paginated = filtered[start:end]
    
    return [ContributionResponse(**c) for c in paginated]


@router.post("/{contribution_id}/review", response_model=ContributionResponse)
async def review_contribution(
    contribution_id: int,
    review: ContributionReview,
    user: dict = Depends(require_hod)
):
    """
    Review a contribution (UC-04, UC-05).
    
    Actions: validate, reject, flag
    """
    contribution = _contributions.get(contribution_id)
    
    if not contribution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contribution not found"
        )
    
    if contribution["status"] not in [ContributionStatus.PENDING, ContributionStatus.UNDER_REVIEW, ContributionStatus.FLAGGED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot review contribution with status: {contribution['status']}"
        )
    
    now = datetime.utcnow()
    
    if review.action == "validate":
        # Finalize credits
        contribution["status"] = ContributionStatus.VALIDATED
        contribution["final_credits"] = contribution["calculated_credits"]
        contribution["reviewer_id"] = user["faculty_id"]
        contribution["review_notes"] = review.notes
        contribution["review_time"] = now
        
        # Update blockchain
        try:
            if blockchain_service.is_connected and contribution["blockchain_id"]:
                await blockchain_service.validate_block(
                    contribution["blockchain_id"],
                    review.notes
                )
        except Exception as e:
            print(f"Blockchain validation failed: {e}")
    
    elif review.action == "reject":
        contribution["status"] = ContributionStatus.REJECTED
        contribution["reviewer_id"] = user["faculty_id"]
        contribution["review_notes"] = review.notes
        contribution["review_time"] = now
        
        # Update blockchain
        try:
            if blockchain_service.is_connected and contribution["blockchain_id"]:
                await blockchain_service.reject_contribution(
                    contribution["blockchain_id"],
                    review.notes
                )
        except Exception as e:
            print(f"Blockchain rejection failed: {e}")
    
    elif review.action == "flag":
        contribution["status"] = ContributionStatus.FLAGGED
        contribution["is_flagged"] = True
        contribution["flag_reason"] = review.notes
        contribution["reviewer_id"] = user["faculty_id"]
        contribution["review_notes"] = review.notes
        contribution["review_time"] = now
        
        # Update blockchain
        try:
            if blockchain_service.is_connected and contribution["blockchain_id"]:
                await blockchain_service.flag_contribution(
                    contribution["blockchain_id"],
                    review.notes
                )
        except Exception as e:
            print(f"Blockchain flagging failed: {e}")
    
    return ContributionResponse(**contribution)


@router.get("/{contribution_id}/evaluation", response_model=EvaluationResponse)
async def get_evaluation_details(
    contribution_id: int,
    user: dict = Depends(get_current_user)
):
    """Get detailed AI evaluation for a contribution."""
    contribution = _contributions.get(contribution_id)
    
    if not contribution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contribution not found"
        )
    
    # Prefer cached evaluation details if available
    cached = contribution.get("evaluation_details")
    if cached and not contribution.get("evaluation_error"):
        quality_score = contribution.get("ai_quality_score", 0)
        novelty_percentage = contribution.get("novelty_percentage", 0)
        benchmark_scores = cached.get("benchmark_scores", {})
    else:
        # Fallback: compute on-demand (can be slow on first run)
        evaluation = rem_service.evaluate_abstract(contribution["abstract"])
        quality_score = evaluation.get("quality_score", 0)
        novelty_percentage = evaluation.get("novelty_percentage", 0)
        benchmark_scores = evaluation.get("benchmark_scores", {})
        contribution["ai_quality_score"] = quality_score
        contribution["novelty_percentage"] = novelty_percentage
        contribution["evaluation_details"] = {
            "benchmark_scores": benchmark_scores,
            "keywords_found": evaluation.get("keywords_found", []),
            "abstract_length": evaluation.get("abstract_length"),
            "evaluation_version": evaluation.get("evaluation_version"),
        }
    
    return EvaluationResponse(
        contribution_id=contribution_id,
        quality_score=quality_score,
        novelty_percentage=novelty_percentage,
        benchmark_scores=benchmark_scores,
        fraud_probability=contribution["fraud_score"],
        is_flagged=contribution["is_flagged"],
        flag_reasons=contribution.get("fraud_reasons", [])
    )


@router.get("/pending/review", response_model=List[ContributionResponse])
async def get_pending_reviews(
    user: dict = Depends(require_hod)
):
    """Get all contributions pending review (for HoD/Admin)."""
    pending = [
        c for c in _contributions.values() 
        if c["status"] in [ContributionStatus.PENDING, ContributionStatus.UNDER_REVIEW, ContributionStatus.FLAGGED]
    ]
    
    # Sort by submission time, flagged first
    pending.sort(key=lambda x: (not x["is_flagged"], x["submission_time"]))
    
    return [ContributionResponse(**c) for c in pending]
