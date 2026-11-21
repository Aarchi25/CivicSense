"""CivicSense administrator console."""

from html import escape

import pandas as pd
import streamlit as st

from frontend import api_client
from frontend.components.ui import (
    _category_badge,
    _status_badge,
    sort_complaints_by_priority,
)


def render_admin_dashboard():
    """Render complaint, department, and user management views."""
    top_c1, top_c2 = st.columns([3, 1])
    with top_c1:
        st.markdown(
            "<h3 style='margin: 0 0 0.5rem 0; color: #0a2540; font-weight: 800;'>Admin</h3>",
            unsafe_allow_html=True,
        )
    with top_c2:
        if st.button("Sign Out", key="admin_top_logout", use_container_width=True):
            st.session_state["token"] = None
            st.session_state["role"] = None
            st.session_state["view"] = "home"
            st.rerun()

    sections = ["Smart Classification", "Department Assignment", "Authority & Users"]
    active_section = st.radio(
        "Admin navigation",
        sections,
        index=0,
        horizontal=True,
        label_visibility="collapsed",
    )

    if active_section == sections[0]:
        _render_complaints()
    elif active_section == sections[1]:
        _render_department_assignment()
    else:
        _render_authority_and_users()


def _render_complaints():
    st.markdown("<h4>Complaints</h4>", unsafe_allow_html=True)
    complaints = api_client.get_all_complaints_admin()
    if not isinstance(complaints, list):
        detail = complaints.get("detail", "Unable to load complaint records.") if isinstance(complaints, dict) else "Unable to load complaint records."
        st.error(f"Unable to load complaints: {detail}")
        return
    if not complaints:
        st.info("No complaints found.")
        return

    prioritized = sort_complaints_by_priority(complaints)
    st.markdown(
        """
        <div class="table-complaint-row table-complaint-header">
            <div>ID</div>
            <div>COMPLAINT TEXT</div>
            <div>CATEGORY</div>
            <div>DEPARTMENT</div>
            <div>TIMESTAMP</div>
            <div>STATUS</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for complaint in prioritized:
        complaint_id = complaint.get("id", "")
        description = str(complaint.get("description", ""))
        complaint_preview = escape(
            description[:65] + ("..." if len(description) > 65 else "")
        )
        department = escape(str(complaint.get("assignedAuthority") or "Unassigned"))
        urgency = complaint.get("urgencyLevel", "Normal")
        try:
            priority_score = float(complaint.get("urgencyScore", 0) or 0)
        except (TypeError, ValueError):
            priority_score = 0.0
        urgency_badge = (
            f"<span class='badge-urgency urgency-{urgency.lower()}' "
            f"style='margin-left: 6px;'>{urgency}</span>"
        )

        st.markdown(
            f"""
            <div class="table-complaint-row">
                <div style="font-weight: 700; color: #1d4ed8;">#{complaint_id[-6:].upper()}</div>
                <div>
                    <div style="font-weight: 600; color: #0f172a;">{complaint_preview}</div>
                    <div>{urgency_badge} <span style="font-size: 0.75rem; color: #334155;">Score {priority_score:.2f}</span></div>
                </div>
                <div>{_category_badge(complaint.get("category", "General"))}</div>
                <div>{department}</div>
                <div style="color: #64748b; font-size: 0.78rem;">{str(complaint.get("createdAt", ""))[:16]}</div>
                <div>{_status_badge(complaint.get("status", "pending"))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_department_assignment():
    st.markdown("<h4>Department Assignment</h4>", unsafe_allow_html=True)

    success_message = st.session_state.pop("department_assignment_success", None)
    if success_message:
        st.success(success_message)

    complaints = api_client.get_all_complaints_admin(sort_by="priority")
    if not isinstance(complaints, list):
        detail = complaints.get("detail", "Unable to load complaint records.") if isinstance(complaints, dict) else "Unable to load complaint records."
        st.error(f"Department assignment unavailable: {detail}")
        return

    complaints = [
        complaint
        for complaint in complaints
        if str(complaint.get("status", "")).strip().lower() == "pending"
        and not complaint.get("departmentAssigned", False)
    ]
    if not complaints:
        st.info("No pending, unassigned complaints to assign.")
        return

    departments = [
        "Water Board",
        "CEB",
        "RDA",
        "Municipal Council",
        "Police Safety",
        "Disaster Management",
    ]
    complaints = sort_complaints_by_priority(complaints)
    options = {
        f"#{complaint.get('id', '')[-6:].upper()} · {complaint.get('description', '')[:60]}": complaint
        for complaint in complaints
    }
    selected_label = st.selectbox("Complaint", list(options))
    complaint = options[selected_label]

    st.write("Description:", complaint.get("description", ""))
    st.write("Category:", complaint.get("category", "General"))
    current_department = complaint.get("assignedAuthority")
    current_index = departments.index(current_department) if current_department in departments else 0
    department = st.selectbox("Department", departments, index=current_index)

    if st.button("Save Department", type="primary"):
        result = api_client.reassign_complaint(complaint.get("id"), department)
        if isinstance(result, dict) and not result.get("error"):
            st.session_state["department_assignment_success"] = "Department assigned successfully."
            st.rerun()
        else:
            detail = result.get("detail", "Unable to update the department.") if isinstance(result, dict) else "Unable to update the department."
            st.error(detail)


def _render_authority_and_users():
    st.markdown("<h4>Authority &amp; Users</h4>", unsafe_allow_html=True)
    officers_tab, citizens_tab, create_tab = st.tabs(
        ["Department Officers", "Registered Citizens", "Create Authority Officer"]
    )

    users = api_client.get_all_users()
    if not isinstance(users, dict) or users.get("error"):
        detail = users.get("detail", "Unable to load users.") if isinstance(users, dict) else "Unable to load users."
        st.error(detail)
        return

    with officers_tab:
        authorities = users.get("authorities", [])
        if authorities:
            frame = pd.DataFrame(authorities)
            columns = [column for column in ("name", "email", "department", "role", "createdAt") if column in frame]
            st.dataframe(frame[columns], use_container_width=True)
        else:
            st.info("No authority officers found.")

    with citizens_tab:
        citizens = users.get("citizens", [])
        if citizens:
            frame = pd.DataFrame(citizens)
            columns = [column for column in ("name", "email", "role", "createdAt") if column in frame]
            st.dataframe(frame[columns], use_container_width=True)
        else:
            st.info("No registered citizens found.")

    with create_tab:
        name = st.text_input("Officer Full Name")
        email = st.text_input("Official Email")
        password = st.text_input("Initial Password", type="password")
        department = st.selectbox(
            "Department",
            ["Water Board", "CEB", "RDA", "Municipal Council", "Police Safety", "Disaster Management"],
        )

        if st.button("Create Officer Account", type="primary"):
            if not name or not email or not password:
                st.error("All fields are required.")
            else:
                result = api_client.create_authority_user(name, email, password, department)
                if isinstance(result, dict) and not result.get("error"):
                    st.success(f"Authority officer created for {name}.")
                    st.rerun()
                else:
                    detail = result.get("detail", "Unable to create the officer account.") if isinstance(result, dict) else "Unable to create the officer account."
                    st.error(detail)
