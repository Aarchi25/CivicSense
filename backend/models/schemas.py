"""
CivicSense – Pydantic v2 schemas for all domain entities.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, EmailStr


# ════════════════════════════════════════════════════════════
#  Enums
# ════════════════════════════════════════════════════════════

class Role(str, Enum):
    CITIZEN = "citizen"
    AUTHORITY = "authority"
    ADMIN = "admin"


class ComplaintStatus(str, Enum):
    PENDING = "pending"
    SEEN = "seen"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class UrgencyLevel(str, Enum):
    CRITICAL = "Critical"
    URGENT = "Urgent"
    NORMAL = "Normal"


class Category(str, Enum):
    WATER = "Water Issue"
    ELECTRICITY = "Electricity Issue"
    ROAD = "Road Issue"
    GARBAGE = "Garbage Issue"
    SAFETY = "Safety Hazard"
    ENVIRONMENTAL = "Environmental Issue"
    DISASTER = "Disaster"


class IdentityRequestStatus(str, Enum):
    NONE = "none"
    REQUESTED = "requested"
    APPROVED = "approved"
    DECLINED = "declined"


# ════════════════════════════════════════════════════════════
#  User schemas
# ════════════════════════════════════════════════════════════

class CitizenRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    phone: str = Field(..., min_length=10, max_length=20)
    location: str = Field(default="", max_length=200)


class CitizenLogin(BaseModel):
    email: EmailStr
    password: str


class CitizenOut(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    location: str
    role: str = "citizen"
    createdAt: datetime


class AuthorityCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    department: str = Field(..., min_length=2, max_length=100)


class AuthorityLogin(BaseModel):
    email: EmailStr
    password: str


class AuthorityOut(BaseModel):
    id: str
    name: str
    email: str
    department: str
    role: str = "authority"
    createdAt: datetime


class AdminLogin(BaseModel):
    email: EmailStr
    password: str


class AdminOut(BaseModel):
    id: str
    name: str
    email: str
    role: str = "admin"


# ════════════════════════════════════════════════════════════
#  Token
# ════════════════════════════════════════════════════════════

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str
    user_id: str


# ════════════════════════════════════════════════════════════
#  Complaint schemas
# ════════════════════════════════════════════════════════════

class NoteItem(BaseModel):
    authorityId: str = ""
    authorityName: str = ""
    text: str
    createdAt: datetime = Field(default_factory=datetime.utcnow)


class IdentityRequest(BaseModel):
    status: IdentityRequestStatus = IdentityRequestStatus.NONE
    requestedBy: str = ""
    requestedAt: Optional[datetime] = None
    respondedAt: Optional[datetime] = None


class ComplaintCreate(BaseModel):
    description: str = Field(..., min_length=10, max_length=5000)
    location: str = Field(..., min_length=2, max_length=300)
    anonymous: bool = False


class ComplaintOut(BaseModel):
    id: str
    description: str
    location: str
    category: str
    confidence: float
    sentiment: float
    urgencyScore: float
    urgencyLevel: str
    assignedAuthority: str
    status: str
    anonymous: bool
    citizenId: str
    citizenName: Optional[str] = None
    imagePath: Optional[str] = None
    summary: str
    keyPhrases: list[str]
    notes: list[NoteItem]
    identityRequest: IdentityRequest
    upvotes: int = 0
    upvotedBy: list[str] = []
    createdAt: datetime
    updatedAt: Optional[datetime] = None


class StatusUpdate(BaseModel):
    status: ComplaintStatus


class NoteCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


# ════════════════════════════════════════════════════════════
#  Community schemas
# ════════════════════════════════════════════════════════════

class CommunityCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str = Field(default="", max_length=500)
    location: str = Field(..., min_length=2, max_length=200)


class CommunityOut(BaseModel):
    id: str
    name: str
    description: str
    location: str
    members: list[str] = []
    createdAt: datetime


class AnnouncementCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    content: str = Field(..., min_length=5, max_length=5000)
    communityId: str


class AnnouncementOut(BaseModel):
    id: str
    title: str
    content: str
    communityId: str
    communityName: str = ""
    createdBy: str
    createdAt: datetime


# ════════════════════════════════════════════════════════════
#  Stats schemas
# ════════════════════════════════════════════════════════════

class OverviewStats(BaseModel):
    total: int
    pending: int
    seen: int
    in_progress: int
    resolved: int
    anonymous_count: int
    registered_count: int
    critical: int
    urgent: int
    normal: int
    resolution_rate: float
