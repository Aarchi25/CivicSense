"""
CivicSense – Complaints router.
Citizen-facing: submit complaints, view own complaints, approve/decline identity requests, upvote.
"""

import os
import re
import uuid
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel

from backend.database import get_db
from backend.core.security import require_citizen, get_current_user
from backend.services.nlp_service import run_nlp_pipeline
from backend.services.urgency_service import compute_urgency
from backend.services.authority_service import get_assigned_authority
from backend.config import get_settings

router = APIRouter(prefix="/api/complaints", tags=["Complaints"])

# ── Upload directory ─────────────────────────────────────────
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

# ── Personal-premises keywords (Rule C) ────────────────────
PERSONAL_PREMISES_KEYWORDS = [
    "my house", "my home", "inside home", "bathroom", "kitchen",
    "bedroom", "living room", "my apartment", "my flat", "toilet",
    "backyard", "my garden", "my property", "dining room",
]

# ── Categories requiring identification (Rule B) ───────────
IDENTITY_REQUIRED_CATEGORIES = {"Water Issue", "Electricity Issue"}


def _detect_personal_premises(text: str) -> bool:
    """Check if the complaint refers to personal premises."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in PERSONAL_PREMISES_KEYWORDS)


def _serialize_complaint(doc: dict) -> dict:
    """Convert a MongoDB complaint document to a JSON-safe dict."""
    doc["id"] = str(doc.pop("_id"))
    # Ensure nested datetimes are serializable
    for note in doc.get("notes", []):
        if isinstance(note.get("createdAt"), datetime):
            note["createdAt"] = note["createdAt"].isoformat()
    ir = doc.get("identityRequest", {})
    if isinstance(ir.get("requestedAt"), datetime):
        ir["requestedAt"] = ir["requestedAt"].isoformat()
    if isinstance(ir.get("respondedAt"), datetime):
        ir["respondedAt"] = ir["respondedAt"].isoformat()
    return doc


class ComplaintPreviewRequest(BaseModel):
    description: str = ""
    category: str | None = None
    anonymous: bool = False


@router.post("/preview")
async def preview_complaint_ai(body: ComplaintPreviewRequest):
    """Run real-time AI classification and urgency estimation on draft text."""
    desc = body.description.strip()
    if len(desc) < 5 and body.category:
        desc = f"{body.category} issue reported requiring prompt inspection."
    elif len(desc) < 5:
        return {
            "category": body.category or "Unclassified",
            "confidence": 0.5 if body.category else 0.0,
            "sentiment": 0.0,
            "urgencyScore": 0.4 if body.category else 0.0,
            "urgencyLevel": "Normal",
            "assignedAuthority": get_assigned_authority(body.category, "") if body.category else "Pending Analysis",
            "summary": f"{body.category} reported." if body.category else "Select category or enter details",
            "keyPhrases": [body.category.lower()] if body.category else [],
            "tips": "Category selected. Description is optional, or you can add specific details.",
        }

    nlp = run_nlp_pipeline(desc)
    category = body.category if body.category and body.category != "Auto-Detect (AI)" else nlp["category"]
    urgency_score, urgency_level = compute_urgency(
        nlp["sentiment"], nlp["confidence"], desc, body.anonymous
    )
    assigned = get_assigned_authority(category, desc)
    is_personal = _detect_personal_premises(desc)

    tips = []
    if is_personal and body.anonymous:
        tips.append("⚠️ Personal-premises detected: Anonymity must be disabled for this complaint.")
    if category in IDENTITY_REQUIRED_CATEGORIES and body.anonymous:
        tips.append(f"⚠️ {category} requires verified citizen identification.")
    if urgency_score >= 0.7:
        tips.append("🚨 High-urgency grievance detected. Priority dispatch will be triggered.")
    if not tips:
        tips.append("✅ Ready for dispatch to responsible department.")

    return {
        "category": category,
        "confidence": nlp["confidence"],
        "sentiment": nlp["sentiment"],
        "urgencyScore": urgency_score,
        "urgencyLevel": urgency_level,
        "assignedAuthority": assigned,
        "summary": nlp["summary"],
        "keyPhrases": nlp["keyPhrases"],
        "isPersonalPremises": is_personal,
        "tips": " | ".join(tips),
    }


# ════════════════════════════════════════════════════════════
#  POST /api/complaints  –  Submit a new complaint
# ════════════════════════════════════════════════════════════

@router.post("", status_code=201)
async def submit_complaint(
    description: str = Form(""),
    category: str | None = Form(None),
    location: str = Form(...),
    anonymous: bool = Form(False),
    image: UploadFile | None = File(None),
    current_user: dict = Depends(require_citizen),
):
    """Submit a new complaint with optional image. Runs the full AI pipeline."""
    db = get_db()
    settings = get_settings()

    desc_clean = description.strip()
    if not desc_clean and category:
        desc_clean = f"{category} reported at {location} requiring civic inspection and repair."
    elif not desc_clean:
        desc_clean = f"Civic grievance reported at {location}."

    # ── Rule C: personal premises require identification ────
    if anonymous and _detect_personal_premises(desc_clean):
        raise HTTPException(
            status_code=400,
            detail="Complaints about personal premises (home, bathroom, etc.) "
            "require identification. Anonymous mode is not available for this type.",
        )

    # ── Run NLP pipeline ────────────────────────────────────
    nlp = run_nlp_pipeline(desc_clean)
    final_category = category if category and category != "Auto-Detect (AI)" else nlp["category"]

    # ── Rule B: Water/Electricity require identification ────
    if anonymous and final_category in IDENTITY_REQUIRED_CATEGORIES:
        anonymous = False  # auto-disable (Rule D)

    # ── Rule D message (inform, don't block) ────────────────
    identity_note = ""
    if final_category in IDENTITY_REQUIRED_CATEGORIES:
        identity_note = (
            f"{final_category} complaints require identification for service verification."
        )

    # ── Urgency ─────────────────────────────────────────────
    urgency_score, urgency_level = compute_urgency(
        nlp["sentiment"], nlp["confidence"], desc_clean, anonymous
    )

    # ── Authority assignment ────────────────────────────────
    assigned = get_assigned_authority(final_category, desc_clean)

    # ── Image handling ──────────────────────────────────────
    image_path = None
    if image:
        if image.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP, GIF images allowed")
        content = await image.read()
        if len(content) > settings.max_image_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"Image must be smaller than {settings.max_image_size_mb} MB",
            )
        ext = image.filename.rsplit(".", 1)[-1] if "." in image.filename else "jpg"
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(content)
        image_path = f"/uploads/{filename}"

    # ── Build document ──────────────────────────────────────
    citizen_name = "" if anonymous else current_user.get("name", "")
    doc = {
        "description": desc_clean,
        "location": location,
        "category": final_category,
        "confidence": nlp["confidence"],
        "sentiment": nlp["sentiment"],
        "urgencyScore": urgency_score,
        "urgencyLevel": urgency_level,
        "assignedAuthority": assigned,
        "departmentAssigned": False,
        "status": "pending",
        "anonymous": anonymous,
        "citizenId": current_user["user_id"],
        "citizenName": citizen_name,
        "imagePath": image_path,
        "summary": nlp["summary"],
        "keyPhrases": nlp["keyPhrases"],
        "notes": [],
        "identityRequest": {
            "status": "none",
            "requestedBy": "",
            "requestedAt": None,
            "respondedAt": None,
        },
        "upvotes": 0,
        "upvotedBy": [],
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": None,
    }
    result = await db.complaints.insert_one(doc)

    response = {
        "id": str(result.inserted_id),
        "description": desc_clean,
        "category": final_category,
        "confidence": nlp["confidence"],
        "urgencyScore": urgency_score,
        "urgencyLevel": urgency_level,
        "assignedAuthority": assigned,
        "summary": nlp["summary"],
        "message": "Complaint submitted successfully",
    }
    if identity_note:
        response["identityNote"] = identity_note
    return response


# ════════════════════════════════════════════════════════════
#  GET /api/complaints/my-complaints
# ════════════════════════════════════════════════════════════

@router.get("/my-complaints")
async def get_my_complaints(current_user: dict = Depends(require_citizen)):
    """Get all complaints submitted by the current citizen."""
    db = get_db()
    cursor = db.complaints.find({"citizenId": current_user["user_id"]}).sort(
        "createdAt", -1
    )
    results = []
    async for doc in cursor:
        results.append(_serialize_complaint(doc))
    return results


# ════════════════════════════════════════════════════════════
#  GET /api/complaints/{id}
# ════════════════════════════════════════════════════════════

@router.get("/{complaint_id}")
async def get_complaint(complaint_id: str, current_user: dict = Depends(get_current_user)):
    """Get a single complaint by ID."""
    db = get_db()
    try:
        oid = ObjectId(complaint_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Complaint ID format")
    doc = await db.complaints.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return _serialize_complaint(doc)


@router.get("/{complaint_id}/public-track")
async def track_complaint_public(complaint_id: str):
    """Public lookup for tracking a complaint status and timeline without login."""
    db = get_db()
    try:
        oid = ObjectId(complaint_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Complaint ID format")
    doc = await db.complaints.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Complaint not found")
    data = _serialize_complaint(doc)
    data["citizenName"] = "Citizen" if not data.get("anonymous") else "Anonymous Citizen"
    data.pop("citizenId", None)
    return data



# ════════════════════════════════════════════════════════════
#  Identity request flow
# ════════════════════════════════════════════════════════════

@router.post("/{complaint_id}/request-identity")
async def request_identity(
    complaint_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Authority requests to reveal identity of anonymous complaint."""
    if current_user["role"] not in ("authority", "admin"):
        raise HTTPException(status_code=403, detail="Only authorities can request identity")

    db = get_db()
    doc = await db.complaints.find_one({"_id": ObjectId(complaint_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if not doc.get("anonymous"):
        raise HTTPException(status_code=400, detail="Complaint is not anonymous")
    if doc.get("identityRequest", {}).get("status") != "none":
        raise HTTPException(status_code=400, detail="Identity already requested or resolved")

    await db.complaints.update_one(
        {"_id": ObjectId(complaint_id)},
        {
            "$set": {
                "identityRequest.status": "requested",
                "identityRequest.requestedBy": current_user["user_id"],
                "identityRequest.requestedAt": datetime.now(timezone.utc),
            }
        },
    )
    return {"message": "Identity reveal request sent to the citizen"}


@router.post("/{complaint_id}/approve-identity")
async def approve_identity(
    complaint_id: str,
    current_user: dict = Depends(require_citizen),
):
    """Citizen approves identity reveal for their anonymous complaint."""
    db = get_db()
    doc = await db.complaints.find_one({"_id": ObjectId(complaint_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if doc["citizenId"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not your complaint")
    if doc.get("identityRequest", {}).get("status") != "requested":
        raise HTTPException(status_code=400, detail="No pending identity request")

    # Reveal identity
    await db.complaints.update_one(
        {"_id": ObjectId(complaint_id)},
        {
            "$set": {
                "identityRequest.status": "approved",
                "identityRequest.respondedAt": datetime.now(timezone.utc),
                "anonymous": False,
                "citizenName": current_user.get("name", ""),
            }
        },
    )
    return {"message": "Identity revealed to the requesting authority"}


@router.post("/{complaint_id}/decline-identity")
async def decline_identity(
    complaint_id: str,
    current_user: dict = Depends(require_citizen),
):
    """Citizen declines identity reveal."""
    db = get_db()
    doc = await db.complaints.find_one({"_id": ObjectId(complaint_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if doc["citizenId"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not your complaint")
    if doc.get("identityRequest", {}).get("status") != "requested":
        raise HTTPException(status_code=400, detail="No pending identity request")

    await db.complaints.update_one(
        {"_id": ObjectId(complaint_id)},
        {
            "$set": {
                "identityRequest.status": "declined",
                "identityRequest.respondedAt": datetime.now(timezone.utc),
            }
        },
    )
    return {"message": "Identity reveal request declined"}


# ════════════════════════════════════════════════════════════
#  Upvote
# ════════════════════════════════════════════════════════════

@router.post("/{complaint_id}/upvote")
async def upvote_complaint(
    complaint_id: str,
    current_user: dict = Depends(require_citizen),
):
    """Toggle upvote on a complaint."""
    db = get_db()
    doc = await db.complaints.find_one({"_id": ObjectId(complaint_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Complaint not found")

    uid = current_user["user_id"]
    upvoted_by = doc.get("upvotedBy", [])

    if uid in upvoted_by:
        # Remove upvote
        await db.complaints.update_one(
            {"_id": ObjectId(complaint_id)},
            {"$pull": {"upvotedBy": uid}, "$inc": {"upvotes": -1}},
        )
        return {"message": "Upvote removed", "upvotes": doc.get("upvotes", 1) - 1}
    else:
        # Add upvote
        await db.complaints.update_one(
            {"_id": ObjectId(complaint_id)},
            {"$push": {"upvotedBy": uid}, "$inc": {"upvotes": 1}},
        )
        return {"message": "Upvoted", "upvotes": doc.get("upvotes", 0) + 1}
