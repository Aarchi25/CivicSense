"""
CivicSense – Streamlit Main Application Entry Point.
Redesigned with proper application flow:
Public Home Page → Dedicated Login/Registration → Role-Based Dashboard (Citizen / Admin / Authority).
"""

import os
import sys
from pathlib import Path

# Ensure project root directory is on sys.path when launched via `streamlit run frontend/app.py`
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

# Must be the first Streamlit command
st.set_page_config(
    page_title="CivicSense – AI Public Grievance Portal",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from frontend import api_client
from frontend.pages.public_home import render_public_home
from frontend.pages.auth_page import render_auth_page
from frontend.pages.citizen_dashboard import render_citizen_dashboard
from frontend.pages.admin_dashboard import render_admin_dashboard
from frontend.pages.authority_dashboard import render_authority_dashboard


def load_custom_css():
    """Load and inject custom government portal CSS."""
    css_path = Path(__file__).parent / "styles" / "custom.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state defaults."""
    defaults = {
        "view": "home",  # "home" | "auth" | "dashboard"
        "auth_tab": "login",  # "login" | "register"
        "token": None,
        "role": None,  # "citizen" | "admin" | "authority"
        "user_name": None,
        "user_email": None,
        "user_id": None,
        "department": None,
        "api_base_url": "http://localhost:8000",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def main():
    """Main application orchestrator."""
    load_custom_css()
    init_session_state()

    token = st.session_state.get("token")
    role = st.session_state.get("role")
    view = st.session_state.get("view", "home")

    # Hide sidebar when on public home or authentication screens
    if not token or view in ("home", "auth"):
        st.markdown(
            """
            <style>
                [data-testid="stSidebar"] { display: none !important; }
                section[data-testid="stSidebar"] { width: 0 !important; }
            </style>
            """,
            unsafe_allow_html=True,
        )

    # ── Application Routing ─────────────────────────────────────
    if not token:
        if view == "auth":
            render_auth_page()
        else:
            render_public_home()
    else:
        # User is authenticated: route to role-specific dashboard
        if role == "citizen":
            render_citizen_dashboard()
        elif role == "admin":
            render_admin_dashboard()
        elif role == "authority":
            render_authority_dashboard()
        else:
            st.error(f"Unrecognized user role: {role}")
            if st.button("Return to Sign In"):
                st.session_state["token"] = None
                st.session_state["role"] = None
                st.session_state["view"] = "auth"
                st.rerun()


if __name__ == "__main__":
    main()
