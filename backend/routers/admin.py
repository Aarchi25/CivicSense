"""
CivicSense – Admin router.
Admin-facing: manage authority users, view all complaints, CSV import.
"""

from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from pymongo import UpdateOne

from backend.database import get_db
from backend.core.security import require_admin, hash_password
from backend.models.schemas import AuthorityCreate, AuthorityOut
from backend.services.csv_service import process_csv
from backend.services.priority_service import priority_sort_pipeline
from backend.services.urgency_service import compute_urgency
from pydantic import BaseModel

class AssignDepartmentRequest(BaseModel):
    assignedAuthority: str

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ════════════════════════════════════════════════════════════
#  Authority user management
# ════════════════════════════════════════════════════════════

@router.post("/authority-users", status_code=201)
async def create_authority_user(
    body: AuthorityCreate,
    current_user: dict = Depends(require_admin),
):
    """Create a new authority user (by admin only)."""
    db = get_db()
    existing = await db.authorities.find_one({"email": body.email})
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    doc = {
        "name": body.name,
        "email": body.email,
        "password": hash_password(body.password),
        "department": body.department,
        "role": "authority",
        "createdAt": datetime.now(timezone.utc),
    }
    result = await db.authorities.insert_one(doc)
    return {
        "id": str(result.inserted_id),
        "name": body.name,
        "email": body.email,
        "department": body.department,
        "message": "Authority user created",
    }


@router.get("/users")
async def list_all_users(current_user: dict = Depends(require_admin)):
    """List all authority users and citizens."""
    db = get_db()

    authorities = []
    async for doc in db.authorities.find():
        authorities.append(
            {
                "id": str(doc["_id"]),
                "name": doc["name"],
                "email": doc["email"],
                "department": doc.get("department", ""),
                "role": "authority",
                "createdAt": doc["createdAt"].isoformat()
                if isinstance(doc.get("createdAt"), datetime)
                else "",
            }
        )

    citizens = []
    async for doc in db.citizens.find():
        citizens.append(
            {
                "id": str(doc["_id"]),
                "name": doc["name"],
                "email": doc["email"],
                "role": "citizen",
                "createdAt": doc["createdAt"].isoformat()
                if isinstance(doc.get("createdAt"), datetime)
                else "",
            }
        )

    return {"authorities": authorities, "citizens": citizens}


@router.get("/complaints")
async def get_all_complaints(
    sort_by: str = Query("priority"),
    current_user: dict = Depends(require_admin),
):
    """View all complaints, sorted by priority or submission date."""
    db = get_db()
    if sort_by == "createdAt":
        cursor = db.complaints.find().sort("createdAt", -1)
    elif sort_by in ("priority", "urgencyScore"):
        cursor = db.complaints.aggregate(priority_sort_pipeline())
    else:
        raise HTTPException(
            status_code=422,
            detail="sort_by must be 'priority', 'urgencyScore', or 'createdAt'.",
        )
    results = []
    urgency_updates = []
    async for doc in cursor:
        urgency_score, urgency_level = compute_urgency(
            float(doc.get("sentiment") or 0),
            float(doc.get("confidence") or 0),
            str(doc.get("description") or ""),
            bool(doc.get("anonymous", False)),
        )
        if (
            float(doc.get("urgencyScore") or 0) != urgency_score
            or doc.get("urgencyLevel") != urgency_level
        ):
            urgency_updates.append(
                UpdateOne(
                    {"_id": doc["_id"]},
                    {
                        "$set": {
                            "urgencyScore": urgency_score,
                            "urgencyLevel": urgency_level,
                        }
                    },
                )
            )
        doc["urgencyScore"] = urgency_score
        doc["urgencyLevel"] = urgency_level
        doc["id"] = str(doc.pop("_id"))
        for note in doc.get("notes", []):
            if isinstance(note.get("createdAt"), datetime):
                note["createdAt"] = note["createdAt"].isoformat()
        results.append(doc)
    if urgency_updates:
        await db.complaints.bulk_write(urgency_updates, ordered=False)
    return results


@router.patch("/complaints/{complaint_id}/assign")
async def assign_department(
    complaint_id: str,
    body: AssignDepartmentRequest,
    current_user: dict = Depends(require_admin),
):
    """Reassign a complaint to a specific authority department (admin only)."""
    db = get_db()
    result = await db.complaints.update_one(
        {"_id": ObjectId(complaint_id)},
        {
            "$set": {
                "assignedAuthority": body.assignedAuthority,
                "departmentAssigned": True,
            }
        },
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return {"message": f"Complaint reassigned to {body.assignedAuthority}", "assignedAuthority": body.assignedAuthority}



# ════════════════════════════════════════════════════════════
#  CSV bulk import
# ════════════════════════════════════════════════════════════

@router.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_admin),
):
    """Upload a CSV file for bulk complaint import."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10 MB limit
        raise HTTPException(status_code=400, detail="CSV file too large (max 10 MB)")

    result = await process_csv(content, current_user["user_id"])
    return result
