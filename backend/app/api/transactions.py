"""
SALF API Routes - Transaction Explorer
Look up blockchain events by transaction hash or wallet address
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_user
from app.core.database import get_db
from app.models.database import (
    Contribution as ContributionORM,
    ContributionStatus as DBStatus,
    User as UserORM,
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])

CATEGORY_LABELS = {
    "refereed_journal": "Refereed Journal",
    "international_book": "International Book",
    "national_book": "National Book",
    "book_chapter": "Book Chapter",
    "international_lecture": "International Lecture / Guest Lecture",
    "national_conference": "National Conference",
    "patent_filed": "Patent Filed",
    "patent_granted": "Patent Granted",
    "editorial_work": "Editorial Work",
    "research_project": "Research Project",
}


def _events_for_contribution(c: ContributionORM, reviewer_wallet: str | None = None) -> list:
    events = []

    if c.blockchain_tx_hash:
        events.append({
            "type": "submission",
            "label": "Contribution Submitted",
            "contribution_id": c.id,
            "blockchain_id": c.blockchain_id,
            "title": c.title,
            "category": c.category.value if c.category else None,
            "category_label": CATEGORY_LABELS.get(c.category.value, c.category.value) if c.category else None,
            "current_status": c.status.value if c.status else None,
            "actor_address": c.faculty_address,
            "actor_role": "faculty",
            "tx_hash": c.blockchain_tx_hash,
            "timestamp": c.submission_time.isoformat() if c.submission_time else None,
            "details": {
                "ipfs_hash": c.ipfs_hash,
                "base_credits": c.base_credits or 0,
                "ai_quality_score": c.ai_quality_score or 0,
                "novelty_percentage": c.novelty_percentage or 0,
                "fraud_score": c.fraud_score or 0,
                "is_flagged": c.is_flagged or False,
            },
        })

    if c.review_time and c.reviewer_id:
        if c.status == DBStatus.VALIDATED:
            rtype, rlabel = "validation", "Contribution Validated"
        elif c.status == DBStatus.REJECTED:
            rtype, rlabel = "rejection", "Contribution Rejected"
        else:
            rtype, rlabel = "flagging", "Contribution Flagged"

        events.append({
            "type": rtype,
            "label": rlabel,
            "contribution_id": c.id,
            "blockchain_id": c.blockchain_id,
            "title": c.title,
            "category": c.category.value if c.category else None,
            "category_label": CATEGORY_LABELS.get(c.category.value, c.category.value) if c.category else None,
            "current_status": c.status.value if c.status else None,
            "actor_address": reviewer_wallet,
            "actor_role": "hod",
            "tx_hash": None,
            "timestamp": c.review_time.isoformat() if c.review_time else None,
            "details": {
                "review_notes": c.review_notes,
                "final_credits": c.final_credits or 0,
                "flag_reason": c.flag_reason,
                "faculty_address": c.faculty_address,
            },
        })

    return events


@router.get("/lookup")
async def lookup_transactions(
    q: str = Query(..., description="Transaction hash (0x + 64 hex chars) or wallet address (0x + 40 hex chars)"),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Look up blockchain activity by transaction hash or wallet address.
    - 66-char input → single transaction lookup
    - 42-char input → all activity for that wallet (submissions as faculty + reviews as HoD)
    """
    q = q.strip().lower()

    if not q.startswith("0x"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must start with 0x — provide a transaction hash (66 chars) or wallet address (42 chars)",
        )

    if len(q) == 66:
        result = await db.execute(
            select(ContributionORM).where(ContributionORM.blockchain_tx_hash == q)
        )
        contribution = result.scalar_one_or_none()

        if not contribution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No contribution found with this transaction hash",
            )

        reviewer_wallet = None
        if contribution.reviewer_id:
            rev = await db.get(UserORM, contribution.reviewer_id)
            if rev:
                reviewer_wallet = rev.wallet_address

        events = _events_for_contribution(contribution, reviewer_wallet)
        events.sort(key=lambda x: x["timestamp"] or "", reverse=True)

        return {
            "query": q,
            "query_type": "tx_hash",
            "wallet_info": None,
            "transactions": events,
            "total": len(events),
        }

    elif len(q) == 42:
        wallet_user_result = await db.execute(
            select(UserORM).where(UserORM.wallet_address == q)
        )
        wallet_user = wallet_user_result.scalar_one_or_none()

        submitted_result = await db.execute(
            select(ContributionORM)
            .where(ContributionORM.faculty_address == q)
            .order_by(ContributionORM.submission_time.desc())
        )
        submitted = submitted_result.scalars().all()

        events: list = []
        submitted_ids: set = set()

        for c in submitted:
            submitted_ids.add(c.id)
            reviewer_wallet = None
            if c.reviewer_id:
                rev = await db.get(UserORM, c.reviewer_id)
                if rev:
                    reviewer_wallet = rev.wallet_address
            events.extend(_events_for_contribution(c, reviewer_wallet))

        if wallet_user:
            reviewed_result = await db.execute(
                select(ContributionORM)
                .where(ContributionORM.reviewer_id == wallet_user.id)
                .order_by(ContributionORM.review_time.desc())
            )
            reviewed = reviewed_result.scalars().all()

            for c in reviewed:
                if c.id not in submitted_ids and c.review_time:
                    if c.status == DBStatus.VALIDATED:
                        rtype, rlabel = "validation", "Contribution Validated"
                    elif c.status == DBStatus.REJECTED:
                        rtype, rlabel = "rejection", "Contribution Rejected"
                    else:
                        rtype, rlabel = "flagging", "Contribution Flagged"

                    events.append({
                        "type": rtype,
                        "label": rlabel,
                        "contribution_id": c.id,
                        "blockchain_id": c.blockchain_id,
                        "title": c.title,
                        "category": c.category.value if c.category else None,
                        "category_label": CATEGORY_LABELS.get(c.category.value, c.category.value) if c.category else None,
                        "current_status": c.status.value if c.status else None,
                        "actor_address": q,
                        "actor_role": "hod",
                        "tx_hash": None,
                        "timestamp": c.review_time.isoformat() if c.review_time else None,
                        "details": {
                            "review_notes": c.review_notes,
                            "final_credits": c.final_credits or 0,
                            "flag_reason": c.flag_reason,
                            "faculty_address": c.faculty_address,
                        },
                    })

        events.sort(key=lambda x: x["timestamp"] or "", reverse=True)

        wallet_info = None
        if wallet_user:
            wallet_info = {
                "name": wallet_user.name,
                "email": wallet_user.email,
                "role": wallet_user.role.value if wallet_user.role else None,
                "employee_id": wallet_user.employee_id,
                "designation": wallet_user.designation.value if wallet_user.designation else None,
                "total_credits": wallet_user.total_credits or 0,
                "is_active": wallet_user.is_active,
            }

        return {
            "query": q,
            "query_type": "wallet_address",
            "wallet_info": wallet_info,
            "transactions": events,
            "total": len(events),
        }

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid length ({len(q)} chars). Provide a 66-char transaction hash or 42-char wallet address.",
        )
