"""
CivicSense – Streamlit API client.
Wraps all requests to the FastAPI backend with resilient error handling.
"""

import requests
import streamlit as st
from typing import Optional


def _base_url() -> str:
    """Get the backend API base URL."""
    return st.session_state.get("api_base_url", "http://localhost:8000")


def _headers() -> dict:
    """Return auth headers if token exists."""
    token = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def _handle_response(resp: requests.Response) -> dict | list | None:
    """Parse response and handle errors."""
    if resp.status_code in (200, 201):
        return resp.json()
    else:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        return {"error": True, "status": resp.status_code, "detail": detail}


def _safe_request(method: str, endpoint: str, **kwargs) -> dict | list | None:
    """Perform a request with full exception handling for network/connection drops."""
    url = f"{_base_url()}{endpoint}"
    if "timeout" not in kwargs:
        kwargs["timeout"] = 15
    try:
        resp = requests.request(method, url, **kwargs)
        return _handle_response(resp)
    except requests.exceptions.ConnectionError:
        return {
            "error": True,
            "status": 503,
            "detail": "Backend server is offline. Please start FastAPI with: uvicorn backend.main:app",
        }
    except requests.exceptions.Timeout:
        return {"error": True, "status": 504, "detail": "Request to backend server timed out"}
    except Exception as e:
        return {"error": True, "status": 500, "detail": str(e)}


# ════════════════════════════════════════════════════════════
#  Auth
# ════════════════════════════════════════════════════════════

def register_citizen(name: str, email: str, password: str, phone: str = "", location: str = ""):
    return _safe_request(
        "POST",
        "/api/citizens/register",
        json={"name": name, "email": email, "password": password, "phone": phone, "location": location},
    )


def login_citizen(email: str, password: str):
    return _safe_request(
        "POST",
        "/api/citizens/login",
        json={"email": email, "password": password},
    )


def login_authority(email: str, password: str):
    return _safe_request(
        "POST",
        "/api/authority/login",
        json={"email": email, "password": password},
    )


def login_admin(email: str, password: str):
    return _safe_request(
        "POST",
        "/api/admin/login",
        json={"email": email, "password": password},
    )


def get_citizen_profile():
    return _safe_request("GET", "/api/citizens/me", headers=_headers())


def forgot_password(email: str):
    return _safe_request("POST", "/api/auth/forgot-password", json={"email": email})


def reset_password(token: str, password: str):
    return _safe_request(
        "POST",
        "/api/auth/reset-password",
        json={"token": token, "password": password},
    )


# ════════════════════════════════════════════════════════════
#  Complaints
# ════════════════════════════════════════════════════════════

def preview_complaint_ai(description: str = "", category: str = "", anonymous: bool = False):
    payload = {"description": description, "anonymous": anonymous}
    if category:
        payload["category"] = category
    return _safe_request(
        "POST",
        "/api/complaints/preview",
        json=payload,
        headers=_headers(),
    )


def submit_complaint(description: str, location: str, category: str = "", anonymous: bool = False, image=None):
    data = {"description": description, "location": location, "anonymous": str(anonymous).lower()}
    if category:
        data["category"] = category
    files = {}
    if image:
        files["image"] = (image.name, image.read(), image.type)

    return _safe_request(
        "POST",
        "/api/complaints",
        data=data,
        files=files if files else None,
        headers=_headers(),
        timeout=60,
    )


def get_my_complaints():
    return _safe_request("GET", "/api/complaints/my-complaints", headers=_headers())


def get_complaint(complaint_id: str):
    return _safe_request("GET", f"/api/complaints/{complaint_id}", headers=_headers())


def track_complaint_public(complaint_id: str):
    return _safe_request("GET", f"/api/complaints/{complaint_id}/public-track")


def upvote_complaint(complaint_id: str):
    return _safe_request("POST", f"/api/complaints/{complaint_id}/upvote", headers=_headers())


def approve_identity(complaint_id: str):
    return _safe_request("POST", f"/api/complaints/{complaint_id}/approve-identity", headers=_headers())


def decline_identity(complaint_id: str):
    return _safe_request("POST", f"/api/complaints/{complaint_id}/decline-identity", headers=_headers())


# ════════════════════════════════════════════════════════════
#  Authority
# ════════════════════════════════════════════════════════════

def get_authority_complaints(
    status_filter: str = "",
    urgency_filter: str = "",
    sort_by: str = "priority",
):
    params = {"sort_by": sort_by}
    if status_filter:
        params["status"] = status_filter
    if urgency_filter:
        params["urgency"] = urgency_filter
    return _safe_request("GET", "/api/authority/complaints", params=params, headers=_headers())


def update_complaint_status(complaint_id: str, new_status: str):
    return _safe_request(
        "PATCH",
        f"/api/authority/complaints/{complaint_id}/status",
        json={"status": new_status},
        headers=_headers(),
    )


def add_note(complaint_id: str, text: str):
    return _safe_request(
        "POST",
        f"/api/authority/complaints/{complaint_id}/notes",
        json={"text": text},
        headers=_headers(),
    )


def request_identity_reveal(complaint_id: str):
    return _safe_request("POST", f"/api/complaints/{complaint_id}/request-identity", headers=_headers())


def upload_resolution_evidence(complaint_id: str, note: str, image=None):
    data = {"note": note}
    files = {}
    if image:
        files["image"] = (image.name, image.read(), image.type)
    return _safe_request(
        "POST",
        f"/api/authority/complaints/{complaint_id}/resolution-evidence",
        data=data,
        files=files if files else None,
        headers=_headers(),
        timeout=30,
    )


# ════════════════════════════════════════════════════════════
#  Admin
# ════════════════════════════════════════════════════════════

def create_authority_user(name: str, email: str, password: str, department: str):
    return _safe_request(
        "POST",
        "/api/admin/authority-users",
        json={"name": name, "email": email, "password": password, "department": department},
        headers=_headers(),
    )


def get_all_users():
    return _safe_request("GET", "/api/admin/users", headers=_headers())


def get_all_complaints_admin(sort_by: str = "priority"):
    return _safe_request(
        "GET",
        "/api/admin/complaints",
        params={"sort_by": sort_by},
        headers=_headers(),
    )


def upload_csv(file):
    files = {"file": (file.name, file.read(), "text/csv")}
    return _safe_request(
        "POST",
        "/api/admin/upload-csv",
        files=files,
        headers=_headers(),
        timeout=120,
    )


def reassign_complaint(complaint_id: str, assigned_authority: str):
    return _safe_request(
        "PATCH",
        f"/api/admin/complaints/{complaint_id}/assign",
        json={"assignedAuthority": assigned_authority},
        headers=_headers(),
    )


# ════════════════════════════════════════════════════════════
#  Stats
# ════════════════════════════════════════════════════════════

def get_overview_stats():
    return _safe_request("GET", "/api/stats/overview", headers=_headers())


def get_category_stats():
    return _safe_request("GET", "/api/stats/category", headers=_headers())


def get_urgent_stats():
    return _safe_request("GET", "/api/stats/urgent", headers=_headers())


def get_location_stats():
    return _safe_request("GET", "/api/stats/location", headers=_headers())


def get_trend_stats(period: str = "daily"):
    return _safe_request("GET", "/api/stats/trends", params={"period": period}, headers=_headers())


# ════════════════════════════════════════════════════════════
#  Community
# ════════════════════════════════════════════════════════════

def list_communities():
    return _safe_request("GET", "/api/community", headers=_headers())


def create_community(name: str, description: str, location: str):
    return _safe_request(
        "POST",
        "/api/community",
        json={"name": name, "description": description, "location": location},
        headers=_headers(),
    )


def join_community(community_id: str):
    return _safe_request("POST", f"/api/community/{community_id}/join", headers=_headers())


def leave_community(community_id: str):
    return _safe_request("POST", f"/api/community/{community_id}/leave", headers=_headers())


def get_announcements(community_id: str):
    return _safe_request("GET", f"/api/community/announcements/{community_id}", headers=_headers())


def create_announcement(title: str, content: str, community_id: str):
    return _safe_request(
        "POST",
        "/api/community/announcements",
        json={"title": title, "content": content, "communityId": community_id},
        headers=_headers(),
    )


def get_community_feed(community_id: str):
    return _safe_request("GET", f"/api/community/{community_id}/feed", headers=_headers())
