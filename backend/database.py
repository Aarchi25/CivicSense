"""
CivicSense – MongoDB async connection using Motor.
Creates indexes for fast queries.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from backend.config import get_settings

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_db() -> None:
    """Open the MongoDB connection and create indexes.
    Falls back to local MongoDB if Atlas URI fails (e.g. SSL/IP whitelist blocks)."""
    global _client, _db
    settings = get_settings()
    
    # 1. Primary connection attempt
    try:
        candidate_client = AsyncIOMotorClient(settings.mongodb_uri, serverSelectionTimeoutMS=3000)
        # Verify connection with a ping
        await candidate_client.admin.command('ping')
        _client = candidate_client
        _db = _client[settings.mongodb_db_name]
        print(f"✅ Connected to MongoDB at: {settings.mongodb_uri[:35]}... (DB: {settings.mongodb_db_name})")
    except Exception as e:
        print(f"⚠️ Primary MongoDB connection failed ({e}). Attempting fallback to local mongodb://localhost:27017...")
        local_uri = "mongodb://localhost:27017"
        try:
            candidate_client = AsyncIOMotorClient(local_uri, serverSelectionTimeoutMS=3000)
            await candidate_client.admin.command('ping')
            _client = candidate_client
            _db = _client[settings.mongodb_db_name]
            print(f"✅ Connected to local MongoDB at {local_uri} (DB: {settings.mongodb_db_name})")
        except Exception as local_err:
            print(f"❌ Failed to connect to local MongoDB: {local_err}")
            raise local_err

    # ── Indexes ──────────────────────────────────────────────
    await _db.complaints.create_index("status")
    await _db.complaints.create_index("assignedAuthority")
    await _db.complaints.create_index("category")
    await _db.complaints.create_index("createdAt")
    await _db.complaints.create_index("citizenId")
    await _db.complaints.create_index("location")
    await _db.citizens.create_index("email", unique=True)
    await _db.authorities.create_index("email", unique=True)
    await _db.communities.create_index("name", unique=True)
    await _db.admins.create_index("email", unique=True)
    await _db.password_resets.create_index("expiresAt", expireAfterSeconds=0)
    await _db.password_resets.create_index("tokenHash", unique=True)

async def close_db() -> None:
    """Gracefully close the MongoDB connection."""
    global _client
    if _client:
        _client.close()


def get_db() -> AsyncIOMotorDatabase:
    """Return the database handle; call connect_db() first."""
    if _db is None:
        raise RuntimeError("Database not connected. Call connect_db() first.")
    return _db
