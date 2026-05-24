"""
SALF API Routes - Contributions
Academic contribution management endpoints
"""
import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.schemas import (
    ContributionResponse, ContributionReview,
    ContributionCategory, ContributionStatus, EvaluationResponse,
)
from app.core.security import get_current_user, require_faculty, require_hod
from app.core.database import get_db, AsyncSessionLocal
from app.models.database import (
    Contribution as ContributionORM,
    ContributionCategory as DBCategory,
    ContributionStatus as DBStatus,
)
from app.services.ipfs_service import ipfs_service
from app.services.evaluation_service import rem_service
from app.services.fraud_detection import fraud_gatekeeper
from app.services.blockchain_service import blockchain_service
from app.core.config import settings

router = APIRouter(prefix="/contributions", tags=["Contributions"])

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


def _to_response(c: ContributionORM) -> ContributionResponse:
    return ContributionResponse(
        id=c.id,
        blockchain_id=c.blockchain_id,
        faculty_id=c.faculty_id,
        faculty_address=c.faculty_address,
        category=ContributionCategory(c.category.value),
        title=c.title,
        abstract=c.abstract,
        ipfs_hash=c.ipfs_hash,
        status=ContributionStatus(c.status.value),
        ai_quality_score=c.ai_quality_score or 0.0,
        novelty_percentage=c.novelty_percentage or 0.0,
        base_credits=c.base_credits or 0.0,
        final_credits=c.final_credits or 0.0,
        reviewer_id=c.reviewer_id,
        review_notes=c.review_notes,
        submission_time=c.submission_time or datetime.utcnow(),
        fraud_score=c.fraud_score or 0.0,
        is_flagged=c.is_flagged or False,
        blockchain_tx_hash=c.blockchain_tx_hash,
    )


async def _run_ai_evaluation(contribution_id: int) -> None:
    """Background task: run REM evaluation and persist results to DB."""
    async with AsyncSessionLocal() as session:
        c = await session.get(ContributionORM, contribution_id)
        if not c:
            return
        try:
            evaluation = rem_service.evaluate_abstract(c.abstract or "")
            quality_score = float(evaluation.get("quality_score") or 0)
            novelty_percentage = float(evaluation.get("novelty_percentage") or 0)
            base_credits = c.base_credits or 0
            calculated = rem_service.calculate_final_credits(base_credits, quality_score, novelty_percentage)

            c.ai_quality_score = quality_score
            c.novelty_percentage = novelty_percentage
            c.calculated_credits = calculated
            c.evaluation_details = json.dumps({
                "benchmark_scores": evaluation.get("benchmark_scores", {}),
                "keywords_found": evaluation.get("keywords_found", []),
                "abstract_length": evaluation.get("abstract_length"),
                "evaluation_version": evaluation.get("evaluation_version"),
            })
            await session.commit()
        except Exception as e:
            c.evaluation_details = json.dumps({"error": str(e)})
            await session.commit()


@router.get("/ipfs/{cid}")
async def get_ipfs_file(cid: str, user: dict = Depends(require_faculty)):
    """Retrieve a contribution file by CID via the IPFS service."""
    try:
        content = await ipfs_service.get_file(cid)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CID not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"IPFS error: {e}")
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
    user: dict = Depends(require_faculty),
    db: AsyncSession = Depends(get_db),
):
    """Submit a new academic contribution (UC-01)."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are allowed")

    file_content = await file.read()
    if len(file_content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds {settings.MAX_FILE_SIZE_MB} MB",
        )
    if len(abstract) < settings.MIN_ABSTRACT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Abstract must be at least {settings.MIN_ABSTRACT_LENGTH} characters",
        )

    metadata = {
        "journal_name": journal_name,
        "isbn": isbn,
        "issn": issn,
        "doi": doi,
        "co_authors": co_authors.split(",") if co_authors else [],
    }

    # 1. Fraud detection
    fraud_result = fraud_gatekeeper.detect_fraud(
        faculty_address=user["address"],
        category=category.value,
        title=title,
        abstract=abstract,
        metadata=metadata,
    )
    if fraud_result["is_flagged"] and fraud_result["fraud_probability"] >= 0.9:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Submission blocked by fraud detection. Contact administrator.",
            headers={"X-Fraud-Reasons": str(fraud_result["flag_reasons"])},
        )

    # 2. Upload to IPFS
    try:
        ipfs_result = await ipfs_service.upload_file(file_content, file.filename)
        ipfs_hash = ipfs_result["cid"]
        metadata_hash = ipfs_result["metadata_hash"]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"IPFS upload failed: {e}")

    # 3. Persist to PostgreSQL
    base_credits = UGC_POINTS.get(category, 0)
    db_status = DBStatus.FLAGGED if fraud_result["is_flagged"] else DBStatus.PENDING
    db_category = DBCategory(category.value)

    contribution = ContributionORM(
        faculty_id=user["faculty_id"],
        faculty_address=user["address"],
        category=db_category,
        title=title,
        abstract=abstract,
        ipfs_hash=ipfs_hash,
        metadata_hash=metadata_hash,
        file_name=file.filename,
        file_size=len(file_content),
        journal_name=journal_name,
        isbn=isbn,
        issn=issn,
        doi=doi,
        co_authors=co_authors,
        status=db_status,
        ai_quality_score=0.0,
        novelty_percentage=0.0,
        base_credits=float(base_credits),
        final_credits=0.0,
        calculated_credits=0.0,
        fraud_score=fraud_result["fraud_probability"],
        is_flagged=fraud_result["is_flagged"],
        flag_reason=", ".join(fraud_result["flag_reasons"]) if fraud_result["is_flagged"] else None,
        fraud_reasons=json.dumps(fraud_result["flag_reasons"]),
        submission_time=datetime.utcnow(),
    )
    db.add(contribution)
    await db.commit()
    await db.refresh(contribution)

    # 4. AI evaluation in background
    background_tasks.add_task(_run_ai_evaluation, contribution.id)

    # 5. Submit to blockchain (best-effort)
    try:
        if blockchain_service.is_connected:
            category_index = list(ContributionCategory).index(category)
            tx_result = await blockchain_service.submit_record(
                category=category_index,
                title=title,
                ipfs_hash=ipfs_hash,
                metadata_hash=metadata_hash,
            )
            contribution.blockchain_id = tx_result.get("contribution_id")
            contribution.blockchain_tx_hash = tx_result.get("tx_hash")
            await db.commit()
            await db.refresh(contribution)
    except Exception as e:
        print(f"Blockchain submission failed: {e}")

    return _to_response(contribution)


@router.get("/pending/review", response_model=List[ContributionResponse])
async def get_pending_reviews(
    user: dict = Depends(require_hod),
    db: AsyncSession = Depends(get_db),
):
    """Get all contributions pending review (HoD/Admin)."""
    result = await db.execute(
        select(ContributionORM).where(
            ContributionORM.status.in_([DBStatus.PENDING, DBStatus.UNDER_REVIEW, DBStatus.FLAGGED])
        ).order_by(ContributionORM.is_flagged.desc(), ContributionORM.submission_time.asc())
    )
    return [_to_response(c) for c in result.scalars().all()]


@router.get("/", response_model=List[ContributionResponse])
async def list_contributions(
    status: Optional[ContributionStatus] = None,
    category: Optional[ContributionCategory] = None,
    page: int = 1,
    page_size: int = 20,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List contributions with optional filtering."""
    query = select(ContributionORM)

    if user["role"] == "faculty":
        query = query.where(ContributionORM.faculty_address == user["address"])
    if status:
        query = query.where(ContributionORM.status == DBStatus(status.value))
    if category:
        query = query.where(ContributionORM.category == DBCategory(category.value))

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return [_to_response(c) for c in result.scalars().all()]


@router.get("/{contribution_id}", response_model=ContributionResponse)
async def get_contribution(
    contribution_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get contribution details by ID."""
    c = await db.get(ContributionORM, contribution_id)
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contribution not found")
    if user["role"] == "faculty" and c.faculty_address != user["address"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return _to_response(c)


@router.post("/{contribution_id}/review", response_model=ContributionResponse)
async def review_contribution(
    contribution_id: int,
    review: ContributionReview,
    user: dict = Depends(require_hod),
    db: AsyncSession = Depends(get_db),
):
    """Review a contribution — validate, reject, or flag (UC-04, UC-05)."""
    c = await db.get(ContributionORM, contribution_id)
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contribution not found")

    reviewable = {DBStatus.PENDING, DBStatus.UNDER_REVIEW, DBStatus.FLAGGED}
    if c.status not in reviewable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot review contribution with status: {c.status.value}",
        )

    now = datetime.utcnow()

    if review.action == "validate":
        c.status = DBStatus.VALIDATED
        # Use AI-calculated credits if available, otherwise base credits
        c.final_credits = c.calculated_credits if c.calculated_credits else c.base_credits
        c.reviewer_id = user["faculty_id"]
        c.review_notes = review.notes
        c.review_time = now

        # Update faculty total_credits on the User record
        from app.models.database import User
        faculty_user = await db.get(User, c.faculty_id)
        if faculty_user:
            faculty_user.total_credits = (faculty_user.total_credits or 0) + c.final_credits

        try:
            if blockchain_service.is_connected and c.blockchain_id:
                await blockchain_service.validate_block(c.blockchain_id, review.notes)
        except Exception as e:
            print(f"Blockchain validation failed: {e}")

    elif review.action == "reject":
        c.status = DBStatus.REJECTED
        c.reviewer_id = user["faculty_id"]
        c.review_notes = review.notes
        c.review_time = now
        try:
            if blockchain_service.is_connected and c.blockchain_id:
                await blockchain_service.reject_contribution(c.blockchain_id, review.notes)
        except Exception as e:
            print(f"Blockchain rejection failed: {e}")

    elif review.action == "flag":
        c.status = DBStatus.FLAGGED
        c.is_flagged = True
        c.flag_reason = review.notes
        c.reviewer_id = user["faculty_id"]
        c.review_notes = review.notes
        c.review_time = now
        try:
            if blockchain_service.is_connected and c.blockchain_id:
                await blockchain_service.flag_contribution(c.blockchain_id, review.notes)
        except Exception as e:
            print(f"Blockchain flagging failed: {e}")

    await db.commit()
    await db.refresh(c)
    return _to_response(c)


@router.get("/{contribution_id}/evaluation", response_model=EvaluationResponse)
async def get_evaluation_details(
    contribution_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed AI evaluation for a contribution."""
    c = await db.get(ContributionORM, contribution_id)
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contribution not found")

    cached = {}
    if c.evaluation_details:
        try:
            cached = json.loads(c.evaluation_details)
        except Exception:
            pass

    if cached and "error" not in cached:
        quality_score = c.ai_quality_score or 0.0
        novelty_percentage = c.novelty_percentage or 0.0
        benchmark_scores = cached.get("benchmark_scores", {})
    else:
        evaluation = rem_service.evaluate_abstract(c.abstract or "")
        quality_score = float(evaluation.get("quality_score") or 0)
        novelty_percentage = float(evaluation.get("novelty_percentage") or 0)
        benchmark_scores = evaluation.get("benchmark_scores", {})
        c.ai_quality_score = quality_score
        c.novelty_percentage = novelty_percentage
        c.evaluation_details = json.dumps({
            "benchmark_scores": benchmark_scores,
            "keywords_found": evaluation.get("keywords_found", []),
            "abstract_length": evaluation.get("abstract_length"),
            "evaluation_version": evaluation.get("evaluation_version"),
        })
        await db.commit()

    fraud_reasons = []
    if c.fraud_reasons:
        try:
            fraud_reasons = json.loads(c.fraud_reasons)
        except Exception:
            fraud_reasons = [c.fraud_reasons]

    return EvaluationResponse(
        contribution_id=contribution_id,
        quality_score=quality_score,
        novelty_percentage=novelty_percentage,
        benchmark_scores=benchmark_scores,
        fraud_probability=c.fraud_score or 0.0,
        is_flagged=c.is_flagged or False,
        flag_reasons=fraud_reasons,
    )
