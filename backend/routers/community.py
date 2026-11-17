"""
CivicSense – Community router.
Location-based communities, announcements, feed, upvote.
"""

from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends

from backend.database import get_db
from backend.core.security import require_citizen, require_admin, get_current_user
from backend.models.schemas import CommunityCreate, AnnouncementCreate

router = APIRouter(prefix="/api/community", tags=["Community"])


# ════════════════════════════════════════════════════════════
#  Community CRUD
# ════════════════════════════════════════════════════════════

@router.post("", status_code=201)
async def create_community(
    body: CommunityCreate,
    current_user: dict = Depends(require_admin),
):
    """Create a new community (admin only)."""
    db = get_db()
    existing = await db.communities.find_one({"name": body.name})
    if existing:
        raise HTTPException(status_code=409, detail="Community name already exists")

    doc = {
        "name": body.name,
        "description": body.description,
        "location": body.location,
        "members": [],
        "createdBy": current_user["user_id"],
        "createdAt": datetime.now(timezone.utc),
    }
    result = await db.communities.insert_one(doc)
    return {"id": str(result.inserted_id), "message": "Community created"}


@router.get("")
async def list_communities(current_user: dict = Depends(get_current_user)):
    """List all communities."""
    db = get_db()
    results = []
    async for doc in db.communities.find().sort("createdAt", -1):
        results.append(
            {
                "id": str(doc["_id"]),
                "name": doc["name"],
                "description": doc.get("description", ""),
                "location": doc["location"],
                "members": doc.get("members", []),
                "memberCount": len(doc.get("members", [])),
                "createdAt": doc["createdAt"].isoformat()
                if isinstance(doc.get("createdAt"), datetime)
                else "",
            }
        )
    return results


@router.post("/{community_id}/join")
async def join_community(
    community_id: str,
    current_user: dict = Depends(require_citizen),
):
    """Join a community."""
    db = get_db()
    doc = await db.communities.find_one({"_id": ObjectId(community_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Community not found")

    uid = current_user["user_id"]
    if uid in doc.get("members", []):
        raise HTTPException(status_code=400, detail="Already a member")

    await db.communities.update_one(
        {"_id": ObjectId(community_id)},
        {"$push": {"members": uid}},
    )
    return {"message": "Joined community"}


@router.post("/{community_id}/leave")
async def leave_community(
    community_id: str,
    current_user: dict = Depends(require_citizen),
):
    """Leave a community."""
    db = get_db()
    doc = await db.communities.find_one({"_id": ObjectId(community_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Community not found")

    uid = current_user["user_id"]
    if uid not in doc.get("members", []):
        raise HTTPException(status_code=400, detail="Not a member")

    await db.communities.update_one(
        {"_id": ObjectId(community_id)},
        {"$pull": {"members": uid}},
    )
    return {"message": "Left community"}


# ════════════════════════════════════════════════════════════
#  Announcements
# ════════════════════════════════════════════════════════════

@router.post("/announcements", status_code=201)
async def create_announcement(
    body: AnnouncementCreate,
    current_user: dict = Depends(require_admin),
):
    """Post an announcement to a community (admin only)."""
    db = get_db()
    community = await db.communities.find_one({"_id": ObjectId(body.communityId)})
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    doc = {
        "title": body.title,
        "content": body.content,
        "communityId": body.communityId,
        "communityName": community["name"],
        "createdBy": current_user["user_id"],
        "createdAt": datetime.now(timezone.utc),
    }
    result = await db.announcements.insert_one(doc)
    return {"id": str(result.inserted_id), "message": "Announcement posted"}


@router.get("/announcements/{community_id}")
async def get_announcements(
    community_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get announcements for a community."""
    db = get_db()
    results = []
    async for doc in db.announcements.find({"communityId": community_id}).sort(
        "createdAt", -1
    ):
        results.append(
            {
                "id": str(doc["_id"]),
                "title": doc["title"],
                "content": doc["content"],
                "communityId": doc["communityId"],
                "communityName": doc.get("communityName", ""),
                "createdBy": doc["createdBy"],
                "createdAt": doc["createdAt"].isoformat()
                if isinstance(doc.get("createdAt"), datetime)
                else "",
            }
        )
    return results


# ════════════════════════════════════════════════════════════
#  Community feed
# ════════════════════════════════════════════════════════════

@router.get("/{community_id}/feed")
async def community_feed(
    community_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get complaints from the community's location area."""
    db = get_db()
    community = await db.communities.find_one({"_id": ObjectId(community_id)})
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")

    location = community["location"]
    cursor = db.complaints.find({"location": {"$regex": location, "$options": "i"}}).sort(
        [("upvotes", -1), ("createdAt", -1)]
    )
    results = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        results.append(doc)
    return results
