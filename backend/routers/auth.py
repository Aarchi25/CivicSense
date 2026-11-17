"""
CivicSense – Authentication router.
Handles citizen registration/login, authority login, admin login.
"""

from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status, Depends

from backend.database import get_db
from backend.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from backend.models.schemas import (
    CitizenRegister,
    CitizenLogin,
    CitizenOut,
    AuthorityLogin,
    AuthorityOut,
    AdminLogin,
    AdminOut,
    TokenResponse,
)

router = APIRouter(prefix="/api", tags=["Auth"])


# ════════════════════════════════════════════════════════════
#  Citizen endpoints
# ════════════════════════════════════════════════════════════

@router.post("/citizens/register", response_model=TokenResponse, status_code=201)
async def register_citizen(body: CitizenRegister):
    """Register a new citizen account."""
    db = get_db()
    existing = await db.citizens.find_one({"email": body.email})
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    doc = {
        "name": body.name,
        "email": body.email,
        "password": hash_password(body.password),
        "phone": body.phone,
        "location": body.location,
        "role": "citizen",
        "createdAt": datetime.now(timezone.utc),
    }
    result = await db.citizens.insert_one(doc)
    user_id = str(result.inserted_id)

    token = create_access_token(
        {"sub": user_id, "role": "citizen", "name": body.name}
    )
    return TokenResponse(
        access_token=token, role="citizen", name=body.name, user_id=user_id
    )


@router.post("/citizens/login", response_model=TokenResponse)
async def login_citizen(body: CitizenLogin):
    """Citizen login."""
    db = get_db()
    user = await db.citizens.find_one({"email": body.email})
    if not user or not verify_password(body.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id = str(user["_id"])
    token = create_access_token(
        {"sub": user_id, "role": "citizen", "name": user["name"]}
    )
    return TokenResponse(
        access_token=token, role="citizen", name=user["name"], user_id=user_id
    )


@router.get("/citizens/me", response_model=CitizenOut)
async def get_citizen_profile(current_user: dict = Depends(get_current_user)):
    """Get the currently logged-in citizen's profile."""
    db = get_db()
    user = await db.citizens.find_one({"_id": ObjectId(current_user["user_id"])})
    if not user:
        raise HTTPException(status_code=404, detail="Citizen not found")
    return CitizenOut(
        id=str(user["_id"]),
        name=user["name"],
        email=user["email"],
        phone=user.get("phone", ""),
        location=user.get("location", ""),
        role="citizen",
        createdAt=user["createdAt"],
    )


# ════════════════════════════════════════════════════════════
#  Authority endpoints
# ════════════════════════════════════════════════════════════

@router.post("/authority/login", response_model=TokenResponse)
async def login_authority(body: AuthorityLogin):
    """Authority user login."""
    db = get_db()
    user = await db.authorities.find_one({"email": body.email})
    if not user or not verify_password(body.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id = str(user["_id"])
    token = create_access_token(
        {"sub": user_id, "role": "authority", "name": user["name"]}
    )
    return TokenResponse(
        access_token=token,
        role="authority",
        name=user["name"],
        user_id=user_id,
        department=user.get("department"),
    )


# ════════════════════════════════════════════════════════════
#  Admin endpoints
# ════════════════════════════════════════════════════════════

@router.post("/admin/login", response_model=TokenResponse)
async def login_admin(body: AdminLogin):
    """Admin login."""
    db = get_db()
    user = await db.admins.find_one({"email": body.email})
    if not user or not verify_password(body.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id = str(user["_id"])
    token = create_access_token(
        {"sub": user_id, "role": "admin", "name": user["name"]}
    )
    return TokenResponse(
        access_token=token, role="admin", name=user["name"], user_id=user_id
    )
