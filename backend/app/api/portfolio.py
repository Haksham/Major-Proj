"""
SALF API Routes - Portfolio
Academic credit portfolio management
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Depends

from app.schemas.schemas import (
    PortfolioSummary, PortfolioDetail, ContributionResponse,
    ContributionCategory, ContributionStatus, DashboardStats
)
from app.core.security import get_current_user, require_hod, require_admin
from app.services.blockchain_service import blockchain_service

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])

# Import contributions storage (in production, this would be database queries)
from app.api.contributions import _contributions, UGC_POINTS


def _calculate_portfolio(faculty_address: str) -> Dict[str, Any]:
    """Calculate portfolio summary for a faculty member."""
    faculty_contributions = [
        c for c in _contributions.values() 
        if c["faculty_address"] == faculty_address
    ]
    
    total_credits = sum(
        c["final_credits"] for c in faculty_contributions 
        if c["status"] == ContributionStatus.VALIDATED
    )
    
    validated = [c for c in faculty_contributions if c["status"] == ContributionStatus.VALIDATED]
    pending = [c for c in faculty_contributions if c["status"] in [ContributionStatus.PENDING, ContributionStatus.UNDER_REVIEW]]
    rejected = [c for c in faculty_contributions if c["status"] == ContributionStatus.REJECTED]
    flagged = [c for c in faculty_contributions if c["status"] == ContributionStatus.FLAGGED]
    
    # Group by category
    contributions_by_category = {}
    credits_by_category = {}
    
    for category in ContributionCategory:
        cat_contributions = [c for c in validated if c["category"] == category]
        contributions_by_category[category.value] = len(cat_contributions)
        credits_by_category[category.value] = sum(c["final_credits"] for c in cat_contributions)
    
    return {
        "total_credits": total_credits,
        "total_contributions": len(faculty_contributions),
        "validated_count": len(validated),
        "pending_count": len(pending),
        "rejected_count": len(rejected),
        "flagged_count": len(flagged),
        "contributions_by_category": contributions_by_category,
        "credits_by_category": credits_by_category,
        "contributions": faculty_contributions
    }


@router.get("/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(
    user: dict = Depends(get_current_user)
):
    """
    Get academic credit portfolio summary for the current user.
    
    This is the main dashboard view for faculty members.
    """
    portfolio = _calculate_portfolio(user["address"])
    
    return PortfolioSummary(
        total_credits=portfolio["total_credits"],
        total_contributions=portfolio["total_contributions"],
        validated_count=portfolio["validated_count"],
        pending_count=portfolio["pending_count"],
        rejected_count=portfolio["rejected_count"],
        flagged_count=portfolio["flagged_count"],
        contributions_by_category=portfolio["contributions_by_category"],
        credits_by_category=portfolio["credits_by_category"]
    )


@router.get("/detail", response_model=PortfolioDetail)
async def get_portfolio_detail(
    user: dict = Depends(get_current_user)
):
    """
    Get detailed academic credit portfolio with all contributions.
    """
    portfolio = _calculate_portfolio(user["address"])
    
    # Get recent activity (last 10 actions)
    contributions = sorted(
        portfolio["contributions"],
        key=lambda x: x["submission_time"],
        reverse=True
    )
    
    recent_activity = []
    for c in contributions[:10]:
        activity = {
            "type": "submission" if c["status"] == ContributionStatus.PENDING else c["status"].value,
            "title": c["title"],
            "category": c["category"].value,
            "timestamp": c["submission_time"].isoformat() if isinstance(c["submission_time"], datetime) else c["submission_time"],
            "credits": c["final_credits"]
        }
        recent_activity.append(activity)
    
    return PortfolioDetail(
        total_credits=portfolio["total_credits"],
        total_contributions=portfolio["total_contributions"],
        validated_count=portfolio["validated_count"],
        pending_count=portfolio["pending_count"],
        rejected_count=portfolio["rejected_count"],
        flagged_count=portfolio["flagged_count"],
        contributions_by_category=portfolio["contributions_by_category"],
        credits_by_category=portfolio["credits_by_category"],
        contributions=[ContributionResponse(**c) for c in contributions],
        recent_activity=recent_activity
    )


@router.get("/faculty/{wallet_address}", response_model=PortfolioSummary)
async def get_faculty_portfolio(
    wallet_address: str,
    user: dict = Depends(require_hod)
):
    """
    Get portfolio summary for a specific faculty member.
    
    Only accessible by HoD and Admin.
    """
    portfolio = _calculate_portfolio(wallet_address.lower())
    
    if portfolio["total_contributions"] == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No contributions found for this faculty member"
        )
    
    return PortfolioSummary(
        total_credits=portfolio["total_credits"],
        total_contributions=portfolio["total_contributions"],
        validated_count=portfolio["validated_count"],
        pending_count=portfolio["pending_count"],
        rejected_count=portfolio["rejected_count"],
        flagged_count=portfolio["flagged_count"],
        contributions_by_category=portfolio["contributions_by_category"],
        credits_by_category=portfolio["credits_by_category"]
    )


@router.get("/blockchain", response_model=Dict[str, Any])
async def get_blockchain_portfolio(
    user: dict = Depends(get_current_user)
):
    """
    Get portfolio directly from blockchain.
    
    This provides the immutable, verified record.
    """
    if not blockchain_service.is_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Blockchain service not available"
        )
    
    try:
        portfolio = blockchain_service.get_academic_portfolio(user["address"])
        contributions = blockchain_service.get_faculty_contributions(user["address"])
        
        return {
            "on_chain_data": portfolio,
            "contribution_ids": contributions,
            "synced_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch blockchain data: {str(e)}"
        )


@router.get("/leaderboard", response_model=List[Dict[str, Any]])
async def get_leaderboard(
    limit: int = 10,
    user: dict = Depends(get_current_user)
):
    """
    Get top contributors leaderboard.
    """
    # Group contributions by faculty
    faculty_credits = {}
    faculty_info = {}
    
    for c in _contributions.values():
        if c["status"] == ContributionStatus.VALIDATED:
            address = c["faculty_address"]
            if address not in faculty_credits:
                faculty_credits[address] = 0
                faculty_info[address] = {
                    "contributions": 0,
                    "faculty_id": c["faculty_id"]
                }
            
            faculty_credits[address] += c["final_credits"]
            faculty_info[address]["contributions"] += 1
    
    # Sort by credits
    sorted_faculty = sorted(
        faculty_credits.items(),
        key=lambda x: x[1],
        reverse=True
    )[:limit]
    
    leaderboard = []
    for rank, (address, credits) in enumerate(sorted_faculty, 1):
        leaderboard.append({
            "rank": rank,
            "wallet_address": address,
            "total_credits": credits,
            "contribution_count": faculty_info[address]["contributions"],
            "is_current_user": address == user["address"]
        })
    
    return leaderboard


@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    user: dict = Depends(require_hod)
):
    """
    Get dashboard statistics for HoD/Admin.
    """
    all_contributions = list(_contributions.values())
    
    # Get unique faculty
    unique_faculty = set(c["faculty_address"] for c in all_contributions)
    
    # Count pending reviews
    pending = [
        c for c in all_contributions 
        if c["status"] in [ContributionStatus.PENDING, ContributionStatus.UNDER_REVIEW, ContributionStatus.FLAGGED]
    ]
    
    # Sum total credits
    total_credits = sum(
        c["final_credits"] for c in all_contributions 
        if c["status"] == ContributionStatus.VALIDATED
    )
    
    # This month's contributions
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month = [
        c for c in all_contributions 
        if isinstance(c["submission_time"], datetime) and c["submission_time"] >= month_start
    ]
    
    # Top contributors
    faculty_credits = {}
    for c in all_contributions:
        if c["status"] == ContributionStatus.VALIDATED:
            address = c["faculty_address"]
            faculty_credits[address] = faculty_credits.get(address, 0) + c["final_credits"]
    
    top_contributors = [
        {"address": addr, "credits": credits}
        for addr, credits in sorted(faculty_credits.items(), key=lambda x: x[1], reverse=True)[:5]
    ]
    
    # Category distribution
    category_dist = {}
    for category in ContributionCategory:
        count = len([c for c in all_contributions if c["category"] == category])
        category_dist[category.value] = count
    
    return DashboardStats(
        total_faculty=len(unique_faculty),
        total_contributions=len(all_contributions),
        pending_reviews=len(pending),
        total_credits_awarded=total_credits,
        contributions_this_month=len(this_month),
        top_contributors=top_contributors,
        category_distribution=category_dist
    )


@router.get("/audit-trail/{wallet_address}", response_model=List[Dict[str, Any]])
async def get_audit_trail(
    wallet_address: str,
    user: dict = Depends(require_hod)
):
    """
    Get immutable audit trail for a faculty member's contributions.
    
    This provides a complete history of all actions on contributions.
    """
    faculty_contributions = [
        c for c in _contributions.values() 
        if c["faculty_address"] == wallet_address.lower()
    ]
    
    audit_trail = []
    for c in sorted(faculty_contributions, key=lambda x: x["submission_time"], reverse=True):
        # Submission event
        audit_trail.append({
            "event": "SUBMISSION",
            "contribution_id": c["id"],
            "title": c["title"],
            "category": c["category"].value,
            "timestamp": c["submission_time"].isoformat() if isinstance(c["submission_time"], datetime) else c["submission_time"],
            "ipfs_hash": c["ipfs_hash"],
            "blockchain_tx": c.get("blockchain_tx_hash")
        })
        
        # Evaluation event
        if c["ai_quality_score"] > 0:
            audit_trail.append({
                "event": "AI_EVALUATION",
                "contribution_id": c["id"],
                "quality_score": c["ai_quality_score"],
                "novelty_percentage": c["novelty_percentage"],
                "timestamp": c["submission_time"].isoformat() if isinstance(c["submission_time"], datetime) else c["submission_time"]
            })
        
        # Review event
        if c["review_time"]:
            audit_trail.append({
                "event": f"REVIEW_{c['status'].value.upper()}",
                "contribution_id": c["id"],
                "reviewer_id": c["reviewer_id"],
                "notes": c["review_notes"],
                "final_credits": c["final_credits"],
                "timestamp": c["review_time"].isoformat() if isinstance(c["review_time"], datetime) else c["review_time"]
            })
    
    return audit_trail
