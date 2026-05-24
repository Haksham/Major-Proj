"""
SALF API Routes - Portfolio
Academic credit portfolio management
"""
from typing import List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.schemas.schemas import (
    PortfolioSummary, PortfolioDetail, ContributionResponse,
    ContributionCategory, ContributionStatus, DashboardStats,
)
from app.core.security import get_current_user, require_hod
from app.core.database import get_db
from app.services.blockchain_service import blockchain_service
from app.models.database import (
    Contribution as ContributionORM,
    User,
    ContributionStatus as DBStatus,
    ContributionCategory as DBCategory,
)
from app.api.contributions import _to_response, UGC_POINTS

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


async def _portfolio_for_address(faculty_address: str, db: AsyncSession) -> Dict[str, Any]:
    """Query DB for portfolio data of a given wallet address."""
    result = await db.execute(
        select(ContributionORM).where(ContributionORM.faculty_address == faculty_address)
    )
    contribs = result.scalars().all()

    validated = [c for c in contribs if c.status == DBStatus.VALIDATED]
    pending = [c for c in contribs if c.status in (DBStatus.PENDING, DBStatus.UNDER_REVIEW)]
    rejected = [c for c in contribs if c.status == DBStatus.REJECTED]
    flagged = [c for c in contribs if c.status == DBStatus.FLAGGED]

    total_credits = sum(c.final_credits or 0 for c in validated)

    contributions_by_category = {}
    credits_by_category = {}
    for cat in ContributionCategory:
        cat_val = validated if True else []
        cat_items = [c for c in validated if c.category.value == cat.value]
        contributions_by_category[cat.value] = len(cat_items)
        credits_by_category[cat.value] = sum(c.final_credits or 0 for c in cat_items)

    return {
        "total_credits": total_credits,
        "total_contributions": len(contribs),
        "validated_count": len(validated),
        "pending_count": len(pending),
        "rejected_count": len(rejected),
        "flagged_count": len(flagged),
        "contributions_by_category": contributions_by_category,
        "credits_by_category": credits_by_category,
        "contributions": contribs,
    }


@router.get("/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get academic credit portfolio summary for the current user."""
    p = await _portfolio_for_address(user["address"], db)
    return PortfolioSummary(
        total_credits=p["total_credits"],
        total_contributions=p["total_contributions"],
        validated_count=p["validated_count"],
        pending_count=p["pending_count"],
        rejected_count=p["rejected_count"],
        flagged_count=p["flagged_count"],
        contributions_by_category=p["contributions_by_category"],
        credits_by_category=p["credits_by_category"],
    )


@router.get("/me", response_model=PortfolioDetail)
async def get_my_portfolio(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Backwards-compatible alias — same as /portfolio/detail."""
    return await get_portfolio_detail(user, db)


@router.get("/statistics", response_model=PortfolioSummary)
async def get_portfolio_statistics(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Backwards-compatible alias — same as /portfolio/summary."""
    return await get_portfolio_summary(user, db)


@router.get("/detail", response_model=PortfolioDetail)
async def get_portfolio_detail(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed portfolio with all contributions."""
    p = await _portfolio_for_address(user["address"], db)
    sorted_contribs = sorted(p["contributions"], key=lambda c: c.submission_time or datetime.min, reverse=True)

    recent_activity = []
    for c in sorted_contribs[:10]:
        recent_activity.append({
            "type": "submission" if c.status == DBStatus.PENDING else c.status.value,
            "title": c.title,
            "category": c.category.value,
            "timestamp": (c.submission_time or datetime.utcnow()).isoformat(),
            "credits": c.final_credits or 0,
        })

    return PortfolioDetail(
        total_credits=p["total_credits"],
        total_contributions=p["total_contributions"],
        validated_count=p["validated_count"],
        pending_count=p["pending_count"],
        rejected_count=p["rejected_count"],
        flagged_count=p["flagged_count"],
        contributions_by_category=p["contributions_by_category"],
        credits_by_category=p["credits_by_category"],
        contributions=[_to_response(c) for c in sorted_contribs],
        recent_activity=recent_activity,
    )


@router.get("/faculty/{wallet_address}", response_model=PortfolioSummary)
async def get_faculty_portfolio(
    wallet_address: str,
    user: dict = Depends(require_hod),
    db: AsyncSession = Depends(get_db),
):
    """Get portfolio summary for a specific faculty member (HoD/Admin only)."""
    p = await _portfolio_for_address(wallet_address.lower(), db)
    if p["total_contributions"] == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No contributions found")
    return PortfolioSummary(
        total_credits=p["total_credits"],
        total_contributions=p["total_contributions"],
        validated_count=p["validated_count"],
        pending_count=p["pending_count"],
        rejected_count=p["rejected_count"],
        flagged_count=p["flagged_count"],
        contributions_by_category=p["contributions_by_category"],
        credits_by_category=p["credits_by_category"],
    )


@router.get("/blockchain", response_model=Dict[str, Any])
async def get_blockchain_portfolio(user: dict = Depends(get_current_user)):
    """Get portfolio directly from the blockchain (immutable record)."""
    if not blockchain_service.is_connected:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Blockchain not available")
    try:
        portfolio = blockchain_service.get_academic_portfolio(user["address"])
        contributions = blockchain_service.get_faculty_contributions(user["address"])
        return {
            "on_chain_data": portfolio,
            "contribution_ids": contributions,
            "synced_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/leaderboard", response_model=List[Dict[str, Any]])
async def get_leaderboard(
    limit: int = 10,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get top contributors leaderboard."""
    result = await db.execute(
        select(
            ContributionORM.faculty_address,
            ContributionORM.faculty_id,
            func.sum(ContributionORM.final_credits).label("total_credits"),
            func.count(ContributionORM.id).label("contribution_count"),
        )
        .where(ContributionORM.status == DBStatus.VALIDATED)
        .group_by(ContributionORM.faculty_address, ContributionORM.faculty_id)
        .order_by(func.sum(ContributionORM.final_credits).desc())
        .limit(limit)
    )
    rows = result.all()

    return [
        {
            "rank": i + 1,
            "wallet_address": row.faculty_address,
            "total_credits": float(row.total_credits or 0),
            "contribution_count": row.contribution_count,
            "is_current_user": row.faculty_address == user["address"],
        }
        for i, row in enumerate(rows)
    ]


@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    user: dict = Depends(require_hod),
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard statistics for HoD/Admin."""
    # Total unique faculty
    faculty_count = (
        await db.execute(
            select(func.count(func.distinct(ContributionORM.faculty_address)))
        )
    ).scalar() or 0

    total_contribs = (await db.execute(select(func.count(ContributionORM.id)))).scalar() or 0

    pending_count = (
        await db.execute(
            select(func.count(ContributionORM.id)).where(
                ContributionORM.status.in_([DBStatus.PENDING, DBStatus.UNDER_REVIEW, DBStatus.FLAGGED])
            )
        )
    ).scalar() or 0

    total_credits = (
        await db.execute(
            select(func.coalesce(func.sum(ContributionORM.final_credits), 0)).where(
                ContributionORM.status == DBStatus.VALIDATED
            )
        )
    ).scalar() or 0.0

    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month = (
        await db.execute(
            select(func.count(ContributionORM.id)).where(
                ContributionORM.submission_time >= month_start
            )
        )
    ).scalar() or 0

    # Top 5 contributors
    top_result = await db.execute(
        select(
            ContributionORM.faculty_address,
            func.sum(ContributionORM.final_credits).label("credits"),
        )
        .where(ContributionORM.status == DBStatus.VALIDATED)
        .group_by(ContributionORM.faculty_address)
        .order_by(func.sum(ContributionORM.final_credits).desc())
        .limit(5)
    )
    top_contributors = [
        {"address": row.faculty_address, "credits": float(row.credits or 0)}
        for row in top_result.all()
    ]

    # Category distribution
    cat_result = await db.execute(
        select(ContributionORM.category, func.count(ContributionORM.id))
        .group_by(ContributionORM.category)
    )
    cat_rows = {row[0].value: row[1] for row in cat_result.all()}
    category_dist = {cat.value: cat_rows.get(cat.value, 0) for cat in ContributionCategory}

    return DashboardStats(
        total_faculty=faculty_count,
        total_contributions=total_contribs,
        pending_reviews=pending_count,
        total_credits_awarded=float(total_credits),
        contributions_this_month=this_month,
        top_contributors=top_contributors,
        category_distribution=category_dist,
    )


@router.get("/audit-trail/{wallet_address}", response_model=List[Dict[str, Any]])
async def get_audit_trail(
    wallet_address: str,
    user: dict = Depends(require_hod),
    db: AsyncSession = Depends(get_db),
):
    """Get immutable audit trail for a faculty member's contributions."""
    result = await db.execute(
        select(ContributionORM)
        .where(ContributionORM.faculty_address == wallet_address.lower())
        .order_by(ContributionORM.submission_time.desc())
    )
    contribs = result.scalars().all()

    trail = []
    for c in contribs:
        ts = (c.submission_time or datetime.utcnow()).isoformat()
        trail.append({
            "event": "SUBMISSION",
            "contribution_id": c.id,
            "title": c.title,
            "category": c.category.value,
            "timestamp": ts,
            "ipfs_hash": c.ipfs_hash,
            "blockchain_tx": c.blockchain_tx_hash,
        })
        if c.ai_quality_score and c.ai_quality_score > 0:
            trail.append({
                "event": "AI_EVALUATION",
                "contribution_id": c.id,
                "quality_score": c.ai_quality_score,
                "novelty_percentage": c.novelty_percentage,
                "timestamp": ts,
            })
        if c.review_time:
            trail.append({
                "event": f"REVIEW_{c.status.value.upper()}",
                "contribution_id": c.id,
                "reviewer_id": c.reviewer_id,
                "notes": c.review_notes,
                "final_credits": c.final_credits,
                "timestamp": c.review_time.isoformat(),
            })

    return trail
