"""
CivicSense – Authority router.
Authority-facing: view department complaints, update status, add notes, request identity.
"""

import os
import uuid
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form

from backend.database import get_db
from backend.core.security import require_authority
from backend.models.schemas import StatusUpdate, NoteCreate
from backend.services.priority_service import priority_sort_pipeline

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

router = APIRouter(prefix="/api/authority", tags=["Authority"])


def _serialize(doc: dict) -> dict:
    """Convert MongoDB doc to JSON-safe dict."""
    doc["id"] = str(doc.pop("_id"))
    for note in doc.get("notes", []):
        if isinstance(note.get("createdAt"), datetime):
            note["createdAt"] = note["createdAt"].isoformat()
    ir = doc.get("identityRequest", {})
    if isinstance(ir.get("requestedAt"), datetime):
        ir["requestedAt"] = ir["requestedAt"].isoformat()
    if isinstance(ir.get("respondedAt"), datetime):
        ir["respondedAt"] = ir["respondedAt"].isoformat()
    return doc


# ════════════════════════════════════════════════════════════
#  GET  – View department complaints (with filters)
# ════════════════════════════════════════════════════════════

@router.get("/complaints")
async def get_authority_complaints(
    status: str | None = Query(None),
    urgency: str | None = Query(None),
    sort_by: str = Query("priority"),
    current_user: dict = Depends(require_authority),
):
    """Get complaints assigned to the authority's department, with optional filters."""
    db = get_db()
    department = current_user.get("department", "")
    if not department:
        raise HTTPException(status_code=400, detail="No department assigned")

    query: dict = {"assignedAuthority": department}
    if status:
        query["status"] = status
    if urgency:
        query["urgencyLevel"] = urgency

    if sort_by == "createdAt":
        cursor = db.complaints.find(query).sort("createdAt", -1)
    elif sort_by == "status":
        cursor = db.complaints.find(query).sort(
            [("status", 1), ("urgencyScore", -1), ("createdAt", 1)]
        )
    elif sort_by in ("priority", "urgencyScore"):
        cursor = db.complaints.aggregate(
            [{"$match": query}, *priority_sort_pipeline()]
        )
    else:
        raise HTTPException(
            status_code=422,
            detail="sort_by must be 'priority', 'urgencyScore', 'status', or 'createdAt'.",
        )

    results = []
    async for doc in cursor:
        results.append(_serialize(doc))
    return results


# ════════════════════════════════════════════════════════════
#  PATCH  – Update complaint status
# ════════════════════════════════════════════════════════════

@router.patch("/complaints/{complaint_id}/status")
async def update_complaint_status(
    complaint_id: str,
    body: StatusUpdate,
    current_user: dict = Depends(require_authority),
):
    """Update complaint status (pending → seen → in_progress → resolved)."""
    db = get_db()
    doc = await db.complaints.find_one({"_id": ObjectId(complaint_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if doc.get("assignedAuthority") != current_user.get("department"):
        raise HTTPException(status_code=403, detail="Not assigned to your department")

    # Validate status transition
    valid_transitions = {
        "pending": ["seen"],
        "seen": ["in_progress"],
        "in_progress": ["resolved"],
        "resolved": [],
    }
    current_status = doc.get("status", "pending")
    if body.status.value not in valid_transitions.get(current_status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{current_status}' to '{body.status.value}'. "
            f"Allowed: {valid_transitions.get(current_status, [])}",
        )

    await db.complaints.update_one(
        {"_id": ObjectId(complaint_id)},
        {
            "$set": {
                "status": body.status.value,
                "updatedAt": datetime.now(timezone.utc),
            }
        },
    )
    return {"message": f"Status updated to {body.status.value}"}


# ════════════════════════════════════════════════════════════
#  POST  – Add a note
# ════════════════════════════════════════════════════════════

@router.post("/complaints/{complaint_id}/notes")
async def add_note(
    complaint_id: str,
    body: NoteCreate,
    current_user: dict = Depends(require_authority),
):
    """Add a note / update to a complaint."""
    db = get_db()
    doc = await db.complaints.find_one({"_id": ObjectId(complaint_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if doc.get("assignedAuthority") != current_user.get("department"):
        raise HTTPException(status_code=403, detail="Not assigned to your department")

    note = {
        "authorityId": current_user["user_id"],
        "authorityName": current_user.get("name", ""),
        "text": body.text,
        "createdAt": datetime.now(timezone.utc),
    }
    await db.complaints.update_one(
        {"_id": ObjectId(complaint_id)},
        {"$push": {"notes": note}, "$set": {"updatedAt": datetime.now(timezone.utc)}},
    )
    return {"message": "Note added"}


@router.post("/complaints/{complaint_id}/resolution-evidence")
async def upload_resolution_evidence(
    complaint_id: str,
    note: str = Form("Issue resolved by authority team."),
    image: UploadFile = File(None),
    current_user: dict = Depends(require_authority),
):
    """Upload resolution evidence image, add note, and optionally mark as resolved."""
    db = get_db()
    doc = await db.complaints.find_one({"_id": ObjectId(complaint_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if doc.get("assignedAuthority") != current_user.get("department"):
        raise HTTPException(status_code=403, detail="Not assigned to your department")

    evidence_path = None
    if image and image.filename:
        if image.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported image format")
        ext = os.path.splitext(image.filename)[1]
        filename = f"res_{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        content = await image.read()
        with open(filepath, "wb") as f:
            f.write(content)
        evidence_path = f"/uploads/{filename}"

    note_obj = {
        "authorityId": current_user["user_id"],
        "authorityName": current_user.get("name", ""),
        "text": f"✅ RESOLUTION EVIDENCE: {note}",
        "createdAt": datetime.now(timezone.utc),
    }

    update_fields = {
        "status": "resolved",
        "resolvedAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc),
    }
    if evidence_path:
        update_fields["resolutionImagePath"] = evidence_path

    await db.complaints.update_one(
        {"_id": ObjectId(complaint_id)},
        {
            "$set": update_fields,
            "$push": {"notes": note_obj},
        },
    )
    return {
        "message": "Resolution evidence saved and status updated to resolved",
        "status": "resolved",
        "resolutionImagePath": evidence_path,
    }
