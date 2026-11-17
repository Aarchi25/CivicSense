
"""
CivicSense - Initial Admin Bootstrap
Creates the first administrator account.
"""

import asyncio
import logging
from datetime import datetime, timezone

from pymongo.errors import DuplicateKeyError

from backend.config import get_settings
from backend.core.security import hash_password
from backend.database import close_db, connect_db, get_db


logger = logging.getLogger(__name__)


async def initialize_bootstrap_admin() -> None:
    """Create the configured bootstrap admin if that email is not registered."""
    settings = get_settings()

    email = settings.bootstrap_admin_email.strip().lower()
    password = settings.bootstrap_admin_password
    name = settings.bootstrap_admin_name.strip() or "CivicSense Admin"

    if not email and not password:
        logger.info("Bootstrap admin credentials are not configured; skipping.")
        return
    if not email or not password:
        raise ValueError(
            "Both BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD must be configured."
        )

    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password cannot exceed 72 bytes.")

    db = get_db()
    existing_admin = await db.admins.find_one({"email": email}, {"_id": 1})
    if existing_admin:
        logger.info("Bootstrap admin %s already exists; skipping creation.", email)
        return

    admin = {
        "name": name,
        "email": email,
        "password": hash_password(password),
        "role": "admin",
        "createdAt": datetime.now(timezone.utc),
    }
    try:
        await db.admins.insert_one(admin)
    except DuplicateKeyError:
        if await db.admins.find_one({"email": email}, {"_id": 1}) is None:
            raise
        logger.info("Bootstrap admin %s already exists; skipping creation.", email)
        return

    logger.info("Bootstrap admin %s created successfully.", email)


async def bootstrap_admin() -> None:
    """Run the bootstrap initializer as a standalone script."""
    await connect_db()
    try:
        await initialize_bootstrap_admin()
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(bootstrap_admin())
