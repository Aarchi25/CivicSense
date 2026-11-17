"""
CivicSense – FastAPI application entry point.
Registers all routers, CORS, static files, rate limiting, and lifecycle hooks.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.bootstrap_admin import initialize_bootstrap_admin
from backend.database import connect_db, close_db
from backend.routers import auth, complaints, authority, admin, stats, community


# ── Rate limiter ─────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)


# ── Lifecycle ────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: connect DB. Shutdown: close DB."""
    await connect_db()
    try:
        await initialize_bootstrap_admin()
        yield
    finally:
        await close_db()


# ── App creation ─────────────────────────────────────────────
app = FastAPI(
    title="CivicSense API",
    description="AI-Powered Public Complaint Management System",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rate limiting ────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Static files (uploads) ──────────────────────────────────
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ── Register routers ────────────────────────────────────────
app.include_router(auth.router)
app.include_router(complaints.router)
app.include_router(authority.router)
app.include_router(admin.router)
app.include_router(stats.router)
app.include_router(community.router)


# ── Root health check ───────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "CivicSense API",
        "status": "running",
        "docs": "/docs",
    }


# ── Global error handler ────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )
