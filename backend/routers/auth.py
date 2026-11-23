"""
CivicSense – Authentication router.
Handles citizen registration/login, authority login, admin login.
"""

from datetime import datetime, timezone, timedelta
import hashlib
import secrets
import smtplib
from email.message import EmailMessage

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
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from backend.config import get_settings

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


def _send_reset_email(to_email: str, reset_url: str) -> None:
    settings = get_settings()
    if not settings.smtp_host:
        raise RuntimeError(
            "Email is not configured. Set SMTP_HOST and SMTP_FROM_EMAIL in the server environment."
        )

    message = EmailMessage()
    message["Subject"] = "CivicSense password reset"
    message["From"] = settings.smtp_from_email or settings.smtp_username
    message["To"] = to_email
    message.set_content(
        "A password reset was requested for your CivicSense account.\n\n"
        f"Reset your password: {reset_url}\n\n"
        f"This link expires in {settings.password_reset_expire_minutes} minutes.\n"
        "If you did not request this, you can ignore this email."
    )

    if settings.smtp_use_tls:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
    else:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)


@router.post("/auth/forgot-password")
@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest):
    """Create a one-time reset token and email it to an existing account."""
    db = get_db()
    email = str(body.email).strip().lower()
    account = None
    role = None

    for collection_name, account_role in (
        ("citizens", "citizen"),
        ("authorities", "authority"),
        ("admins", "admin"),
    ):
        account = await getattr(db, collection_name).find_one({"email": email})
        if account:
            role = account_role
            break

    generic_message = "If an account exists for this email, a password reset link has been sent."
    if not account:
        return {"message": generic_message}

    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.password_reset_expire_minutes
    )

    await db.password_resets.delete_many({"userId": str(account["_id"]), "role": role})
    await db.password_resets.insert_one(
        {
            "tokenHash": token_hash,
            "userId": str(account["_id"]),
            "role": role,
            "email": email,
            "expiresAt": expires_at,
            "createdAt": datetime.now(timezone.utc),
        }
    )

    separator = "&" if "?" in settings.frontend_base_url else "?"
    reset_url = f"{settings.frontend_base_url.rstrip('/')}{separator}reset_token={token}"
    try:
        _send_reset_email(email, reset_url)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to send reset email: {str(exc)}",
        )

    return {"message": generic_message}


@router.post("/auth/reset-password")
@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest):
    """Reset a password using a valid, unused reset token."""
    db = get_db()
    token_hash = hashlib.sha256(body.token.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc)
    reset = await db.password_resets.find_one(
        {"tokenHash": token_hash, "expiresAt": {"$gt": now}}
    )
    if not reset:
        raise HTTPException(
            status_code=400,
            detail="Reset link is invalid or has expired",
        )

    collection_name = {
        "citizen": "citizens",
        "authority": "authorities",
        "admin": "admins",
    }.get(reset["role"])
    if not collection_name:
        raise HTTPException(status_code=400, detail="Reset link is invalid")

    result = await getattr(db, collection_name).update_one(
        {"_id": ObjectId(reset["userId"])},
        {"$set": {"password": hash_password(body.password)}},
    )
    if result.matched_count != 1:
        raise HTTPException(status_code=400, detail="Reset account no longer exists")

    await db.password_resets.delete_one({"tokenHash": token_hash})
    return {"message": "Password reset successfully. You can now sign in."}
