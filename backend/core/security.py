"""
CivicSense – JWT authentication, password hashing, and role-based guards.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import bcrypt

from backend.config import get_settings
from backend.database import get_db

# ── Password hashing ────────────────────────────────────────
security_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a plain-text password with bcrypt."""
    pw_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    pw_bytes = plain.encode("utf-8")[:72]
    hashed_bytes = hashed.encode("utf-8")
    return bcrypt.checkpw(pw_bytes, hashed_bytes)



# ── JWT helpers ──────────────────────────────────────────────

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT with an expiry."""
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT; raises HTTPException on failure."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


# ── Role-based dependencies ─────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> dict:
    """Extract and validate the user from the Bearer token."""
    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    role = payload.get("role")
    if not user_id or not role:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return {"user_id": user_id, "role": role, "name": payload.get("name", "")}


async def require_citizen(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Only citizens may access this endpoint."""
    if current_user["role"] != "citizen":
        raise HTTPException(status_code=403, detail="Citizens only")
    return current_user


async def require_authority(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Only authority users may access this endpoint."""
    if current_user["role"] != "authority":
        raise HTTPException(status_code=403, detail="Authority users only")
    # Attach department for filtering
    db = get_db()
    from bson import ObjectId
    auth = await db.authorities.find_one({"_id": ObjectId(current_user["user_id"])})
    if auth:
        current_user["department"] = auth.get("department", "")
    return current_user


async def require_admin(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Only admins may access this endpoint."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")
    return current_user
