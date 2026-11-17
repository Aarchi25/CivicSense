"""
CivicSense – Stats router.
Provides analytics endpoints for dashboard charts.
"""

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, Query

from backend.database import get_db
from backend.core.security import get_current_user

router = APIRouter(prefix="/api/stats", tags=["Stats"])


# ════════════════════════════════════════════════════════════
#  Overview
# ════════════════════════════════════════════════════════════

@router.get("/overview")
async def overview_stats(current_user: dict = Depends(get_current_user)):
    """Aggregate overview statistics."""
    db = get_db()
    pipeline = [
        {
            "$group": {
                "_id": None,
                "total": {"$sum": 1},
                "pending": {
                    "$sum": {"$cond": [{"$eq": ["$status", "pending"]}, 1, 0]}
                },
                "seen": {
                    "$sum": {"$cond": [{"$eq": ["$status", "seen"]}, 1, 0]}
                },
                "in_progress": {
                    "$sum": {"$cond": [{"$eq": ["$status", "in_progress"]}, 1, 0]}
                },
                "resolved": {
                    "$sum": {"$cond": [{"$eq": ["$status", "resolved"]}, 1, 0]}
                },
                "anonymous_count": {
                    "$sum": {"$cond": [{"$eq": ["$anonymous", True]}, 1, 0]}
                },
                "registered_count": {
                    "$sum": {"$cond": [{"$eq": ["$anonymous", False]}, 1, 0]}
                },
                "critical": {
                    "$sum": {"$cond": [{"$eq": ["$urgencyLevel", "Critical"]}, 1, 0]}
                },
                "urgent": {
                    "$sum": {"$cond": [{"$eq": ["$urgencyLevel", "Urgent"]}, 1, 0]}
                },
                "normal": {
                    "$sum": {"$cond": [{"$eq": ["$urgencyLevel", "Normal"]}, 1, 0]}
                },
            }
        }
    ]
    result = await db.complaints.aggregate(pipeline).to_list(1)
    if result:
        data = result[0]
        data.pop("_id", None)
        total = data.get("total", 0)
        resolved = data.get("resolved", 0)
        data["resolution_rate"] = round(resolved / total * 100, 1) if total else 0
        return data
    return {
        "total": 0, "pending": 0, "seen": 0, "in_progress": 0,
        "resolved": 0, "anonymous_count": 0, "registered_count": 0,
        "critical": 0, "urgent": 0, "normal": 0, "resolution_rate": 0,
    }


# ════════════════════════════════════════════════════════════
#  Category breakdown
# ════════════════════════════════════════════════════════════

@router.get("/category")
async def category_stats(current_user: dict = Depends(get_current_user)):
    """Complaints count per category."""
    db = get_db()
    pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    results = await db.complaints.aggregate(pipeline).to_list(20)
    return [{"category": r["_id"], "count": r["count"]} for r in results]


# ════════════════════════════════════════════════════════════
#  Urgent complaints
# ════════════════════════════════════════════════════════════

@router.get("/urgent")
async def urgent_complaints(current_user: dict = Depends(get_current_user)):
    """List Critical and Urgent complaints."""
    db = get_db()
    cursor = (
        db.complaints.find(
            {"urgencyLevel": {"$in": ["Critical", "Urgent"]}}
        )
        .sort("urgencyScore", -1)
        .limit(50)
    )
    results = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        results.append(doc)
    return results


# ════════════════════════════════════════════════════════════
#  Location breakdown
# ════════════════════════════════════════════════════════════

@router.get("/location")
async def location_stats(current_user: dict = Depends(get_current_user)):
    """Complaints count per location."""
    db = get_db()
    pipeline = [
        {"$group": {"_id": "$location", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20},
    ]
    results = await db.complaints.aggregate(pipeline).to_list(20)
    return [{"location": r["_id"], "count": r["count"]} for r in results]


# ════════════════════════════════════════════════════════════
#  Trends (daily/weekly/monthly)
# ════════════════════════════════════════════════════════════

@router.get("/trends")
async def trend_stats(
    period: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    current_user: dict = Depends(get_current_user),
):
    """Complaint trends over time."""
    db = get_db()

    if period == "daily":
        date_format = "%Y-%m-%d"
        group_id = {
            "$dateToString": {"format": "%Y-%m-%d", "date": "$createdAt"}
        }
    elif period == "weekly":
        date_format = "%Y-W%V"
        group_id = {
            "$dateToString": {"format": "%Y-W%U", "date": "$createdAt"}
        }
    else:  # monthly
        date_format = "%Y-%m"
        group_id = {
            "$dateToString": {"format": "%Y-%m", "date": "$createdAt"}
        }

    pipeline = [
        {"$group": {"_id": group_id, "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
        {"$limit": 60},
    ]
    results = await db.complaints.aggregate(pipeline).to_list(60)
    return [{"date": r["_id"], "count": r["count"]} for r in results]
