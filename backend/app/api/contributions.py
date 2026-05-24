"""
SALF API Routes - Contributions
Academic contribution management endpoints
"""
import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import Response
from sqlalchemy.exc import IntegrityError
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


def _ledger_write_ready() -> bool:
    return bool(
        blockchain_service.is_connected
        and blockchain_service.account
        and blockchain_service.contracts.get("academic_credit")
    )


async def _ensure_blockchain_link(contribution: ContributionORM) -> None:
    """Set contribution.blockchain_id by matching IPFS on-chain or registering if missing (mirrors submit flow)."""
    if contribution.blockchain_id:
        return
    if not contribution.faculty_address or not contribution.ipfs_hash:
        return

    resolved = blockchain_service.resolve_contribution_id_by_ipfs(
        contribution.ipfs_hash,
        contribution.faculty_address,
    )
    if resolved is not None:
        contribution.blockchain_id = resolved
        return

    if not contribution.metadata_hash:
        return
    try:
        cat = ContributionCategory(contribution.category.value)
        category_index = list(ContributionCategory).index(cat)
    except ValueError:
        return
    try:
        tx_result = await blockchain_service.submit_record(
            category=category_index,
            title=contribution.title,
            ipfs_hash=contribution.ipfs_hash,
            metadata_hash=contribution.metadata_hash,
        )
        new_id = tx_result.get("contribution_id")
        if not new_id:
            new_id = blockchain_service.resolve_contribution_id_by_ipfs(
                contribution.ipfs_hash,
                contribution.faculty_address,
            )
        if new_id:
            contribution.blockchain_id = new_id
        tx_hash = tx_result.get("tx_hash")
        if tx_hash and not contribution.blockchain_tx_hash:
            contribution.blockchain_tx_hash = tx_hash
    except Exception as e:
        print(f"Could not link contribution to chain before review: {e}")


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
        review_tx_hash=c.review_tx_hash,
    )


async def _run_ai_evaluation(contribution_id: int) -> None:
    """Background task: Claude LLM evaluation + gatekeeper fraud check."""
    import httpx
    async with AsyncSessionLocal() as session:
        c = await session.get(ContributionORM, contribution_id)
        if not c:
            return

        # ── 1. LLM quality / novelty evaluation ──────────────────────────────
        try:
            evaluation = rem_service.evaluate_abstract(
                c.abstract or "",
                title=c.title or "",
                category=c.category.value if c.category else "",
            )
            quality_score = float(evaluation.get("quality_score") or 0)
            novelty_percentage = float(evaluation.get("novelty_percentage") or 0)
            base_credits = c.base_credits or 0
            calculated = rem_service.calculate_final_credits(base_credits, quality_score, novelty_percentage)

            c.ai_quality_score = quality_score
            c.novelty_percentage = novelty_percentage
            c.calculated_credits = calculated
            c.evaluation_details = json.dumps({
                "benchmark_scores": evaluation.get("benchmark_scores", {}),
                "summary": evaluation.get("summary", ""),
                "strengths": evaluation.get("strengths", []),
                "concerns": evaluation.get("concerns", []),
                "evaluation_version": evaluation.get("evaluation_version"),
            })
        except Exception as e:
            c.evaluation_details = json.dumps({"error": str(e)})

        # ── 2. Gatekeeper fraud / duplicate check (ml sidecar) ───────────────
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{settings.ML_SERVICE_URL}/gatekeeper/check",
                    json={
                        "text": c.abstract or "",
                        "corpus": [],          # TODO: pass existing abstracts for duplicate check
                        "faculty_id": str(c.faculty_id),
                    },
                )
                if resp.status_code == 200:
                    gk = resp.json()
                    c.fraud_score = float(gk.get("anomaly_score", 0))
                    if not gk.get("is_authentic", True):
                        c.is_flagged = True
                        flags = []
                        if gk.get("is_duplicate"):
                            flags.append(f"Duplicate detected (score {gk.get('duplicate_score', 0):.2f})")
                        if gk.get("is_ai_generated"):
                            flags.append(f"Possible AI-generated text (prob {gk.get('ai_probability', 0):.2f})")
                        if gk.get("is_anomalous"):
                            flags.append(f"Submission anomaly detected (score {gk.get('anomaly_score', 0):.2f})")
                        c.flag_reason = "; ".join(flags)
        except Exception as e:
            # Gatekeeper is optional — log but don't fail the submission
            print(f"Gatekeeper check skipped: {e}")

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
    # High fraud scores are reviewed by HoD — never hard-block legitimate faculty submissions

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
    try:
        await db.commit()
        await db.refresh(contribution)
    except IntegrityError as e:
        await db.rollback()
        if "ix_contributions_metadata_hash" in str(e.orig):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This file has already been submitted. Duplicate submissions are not allowed.",
            )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error during submission.")

    # 4. Persist blockchain submission before returning so the caller can see the tx hash
    try:
        if _ledger_write_ready():
            category_index = list(ContributionCategory).index(category)
            tx_result = await blockchain_service.submit_record(
                category=category_index,
                title=title,
                ipfs_hash=ipfs_hash,
                metadata_hash=metadata_hash,
            )
            contribution.blockchain_id = tx_result.get("contribution_id")
            if not contribution.blockchain_id:
                contribution.blockchain_id = blockchain_service.resolve_contribution_id_by_ipfs(
                    ipfs_hash,
                    user["address"],
                )
            contribution.blockchain_tx_hash = tx_result.get("tx_hash")
            await db.commit()
            await db.refresh(contribution)
    except Exception as e:
        print(f"Blockchain submission failed: {e}")

    # 5. AI evaluation continues in background
    background_tasks.add_task(_run_ai_evaluation, contribution.id)

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

    if user["role"] in ("faculty", "hod"):
        query = query.where(ContributionORM.faculty_address == user["address"])
    if status:
        query = query.where(ContributionORM.status == DBStatus(status.value))
    if category:
        query = query.where(ContributionORM.category == DBCategory(category.value))

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return [_to_response(c) for c in result.scalars().all()]


@router.get("/department/faculty")
async def get_department_faculty_stats(
    user: dict = Depends(require_hod),
    db: AsyncSession = Depends(get_db),
):
    """Faculty list with contribution stats for the HoD's department."""
    from app.models.database import User as UserORM
    hod = await db.get(UserORM, user["faculty_id"])
    if not hod or not hod.department_id:
        return []

    dept_result = await db.execute(
        select(UserORM).where(
            UserORM.department_id == hod.department_id,
            UserORM.is_active == True,
        ).order_by(UserORM.name)
    )
    faculty_list = dept_result.scalars().all()

    output = []
    for f in faculty_list:
        c_result = await db.execute(
            select(ContributionORM).where(ContributionORM.faculty_address == f.wallet_address)
        )
        contribs = c_result.scalars().all()
        output.append({
            "id": f.id,
            "name": f.name,
            "email": f.email,
            "wallet_address": f.wallet_address,
            "role": f.role.value,
            "designation": f.designation.value if f.designation else None,
            "total_credits": f.total_credits or 0.0,
            "total_contributions": len(contribs),
            "pending": sum(1 for c in contribs if c.status.value in ("pending", "under_review")),
            "validated": sum(1 for c in contribs if c.status.value == "validated"),
            "rejected": sum(1 for c in contribs if c.status.value == "rejected"),
        })
    return output


@router.get("/department/contributions", response_model=List[ContributionResponse])
async def get_department_contributions(
    faculty_address: Optional[str] = None,
    user: dict = Depends(require_hod),
    db: AsyncSession = Depends(get_db),
):
    """All contributions from the HoD's department, optionally filtered by a faculty address."""
    from app.models.database import User as UserORM
    hod = await db.get(UserORM, user["faculty_id"])
    if not hod or not hod.department_id:
        return []

    dept_result = await db.execute(
        select(UserORM).where(UserORM.department_id == hod.department_id)
    )
    dept_addresses = {u.wallet_address for u in dept_result.scalars().all()}
    if not dept_addresses:
        return []

    query = select(ContributionORM).where(ContributionORM.faculty_address.in_(dept_addresses))
    if faculty_address:
        query = query.where(ContributionORM.faculty_address == faculty_address.lower())
    query = query.order_by(ContributionORM.submission_time.desc())

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

    if _ledger_write_ready():
        await _ensure_blockchain_link(c)

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
            if _ledger_write_ready() and c.blockchain_id:
                st = blockchain_service.get_contribution_chain_status(c.blockchain_id)
                if st == 2:
                    c.review_tx_hash = blockchain_service.get_review_tx_hash(
                        c.blockchain_id, "validated"
                    )
                else:
                    await blockchain_service.ensure_pending_moves_to_under_review(
                        c.blockchain_id,
                        c.ai_quality_score or 0,
                        c.novelty_percentage or 0,
                    )
                    tx_result = await blockchain_service.validate_block(
                        c.blockchain_id, review.notes
                    )
                    c.review_tx_hash = tx_result.get("tx_hash")
                    if not c.review_tx_hash:
                        c.review_tx_hash = blockchain_service.get_review_tx_hash(
                            c.blockchain_id, "validated"
                        )
        except Exception as e:
            print(f"Blockchain validation failed: {e}")
            if c.blockchain_id:
                c.review_tx_hash = blockchain_service.get_review_tx_hash(c.blockchain_id, "validated")

    elif review.action == "reject":
        c.status = DBStatus.REJECTED
        c.reviewer_id = user["faculty_id"]
        c.review_notes = review.notes
        c.review_time = now
        try:
            if _ledger_write_ready() and c.blockchain_id:
                tx_result = await blockchain_service.reject_contribution(c.blockchain_id, review.notes)
                c.review_tx_hash = tx_result.get("tx_hash")
                if not c.review_tx_hash:
                    c.review_tx_hash = blockchain_service.get_review_tx_hash(c.blockchain_id, "rejected")
        except Exception as e:
            print(f"Blockchain rejection failed: {e}")
            if c.blockchain_id:
                c.review_tx_hash = blockchain_service.get_review_tx_hash(c.blockchain_id, "rejected")

    elif review.action == "flag":
        c.status = DBStatus.FLAGGED
        c.is_flagged = True
        c.flag_reason = review.notes
        c.reviewer_id = user["faculty_id"]
        c.review_notes = review.notes
        c.review_time = now
        try:
            if _ledger_write_ready() and c.blockchain_id:
                tx_result = await blockchain_service.flag_contribution(c.blockchain_id, review.notes)
                c.review_tx_hash = tx_result.get("tx_hash")
                if not c.review_tx_hash:
                    c.review_tx_hash = blockchain_service.get_review_tx_hash(c.blockchain_id, "flagged")
        except Exception as e:
            print(f"Blockchain flagging failed: {e}")
            if c.blockchain_id:
                c.review_tx_hash = blockchain_service.get_review_tx_hash(c.blockchain_id, "flagged")

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
        evaluation = rem_service.evaluate_abstract(
            c.abstract or "",
            title=c.title or "",
            category=c.category.value if c.category else "",
        )
        quality_score = float(evaluation.get("quality_score") or 0)
        novelty_percentage = float(evaluation.get("novelty_percentage") or 0)
        benchmark_scores = evaluation.get("benchmark_scores", {})
        c.ai_quality_score = quality_score
        c.novelty_percentage = novelty_percentage
        c.evaluation_details = json.dumps({
            "benchmark_scores": benchmark_scores,
            "summary": evaluation.get("summary", ""),
            "strengths": evaluation.get("strengths", []),
            "concerns": evaluation.get("concerns", []),
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
