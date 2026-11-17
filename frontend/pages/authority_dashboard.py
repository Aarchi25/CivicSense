"""
CivicSense – Department Authority Operations Portal.
Department-isolated operations for Water Board, CEB, RDA, Municipal, Police, and Disaster Management.
"""

import streamlit as st

from frontend import api_client
from frontend.components.ui import (
    render_portal_metric,
    render_complaint_card,
    render_timeline,
    render_photo_compare,
    render_section_title,
    sort_complaints_by_priority,
)


def render_authority_dashboard():
    """Main departmental officer dashboard."""
    user_name = st.session_state.get("user_name", "Department Officer")
    dept = st.session_state.get("department", "Public Works Department")

    # ── Top Bar ─────────────────────────────────────────────────
    nav_c1, nav_c2, nav_c3 = st.columns([3, 1.2, 1])
    with nav_c1:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 0.5rem;">
                <span style="font-size: 2rem;">🏢</span>
                <div>
                    <h3 style="margin: 0; color: #0a2540; font-weight: 800;">{dept} Operations Desk</h3>
                    <p style="margin: 0; font-size: 0.8rem; color: #64748b;">
                        Officer: <b>{user_name}</b> · Departmental Jurisdiction Active
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with nav_c2:
        from frontend.i18n import render_language_selector
        render_language_selector()
    with nav_c3:
        if st.button("🚪 Sign Out", key="auth_top_logout", use_container_width=True):
            st.session_state["token"] = None
            st.session_state["role"] = None
            st.session_state["view"] = "home"
            st.rerun()

    # ── Horizontal Nav Tabs ─────────────────────────────────────
    tabs = [
        "📋 Department Queue",
        "🔧 Action & Resolution",
    ]

    active_tab = st.radio(
        "Authority Nav",
        tabs,
        index=0,
        horizontal=True,
        label_visibility="collapsed",
    )

    st.markdown("<hr style='margin: 0.4rem 0 1.25rem 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)

    # ── Route Tab ───────────────────────────────────────────────
    if active_tab == "📋 Department Queue":
        _render_department_queue(dept)
    elif active_tab == "🔧 Action & Resolution":
        _render_action_and_resolution(dept)


# ════════════════════════════════════════════════════════════════
#  1. Department Queue
# ════════════════════════════════════════════════════════════════
def _render_department_queue(dept: str):
    render_section_title(f"{dept} Grievances Queue", f"All public complaints assigned specifically to {dept}")

    # Fetch complaints
    res = api_client.get_authority_complaints(sort_by="priority")
    if not isinstance(res, list):
        detail = res.get("detail", "Unable to load department complaints.") if isinstance(res, dict) else "Unable to load department complaints."
        st.error(f"Department queue unavailable: {detail}")
        return
    complaints = sort_complaints_by_priority(res)

    total_c = len(complaints)
    pending_c = sum(1 for c in complaints if c.get("status") in ("pending", "seen"))
    in_prog_c = sum(1 for c in complaints if c.get("status") == "in_progress")
    resolved_c = sum(1 for c in complaints if c.get("status") == "resolved")
    high_priority_c = sum(
        c.get("status") != "resolved" and c.get("urgencyLevel") in ("Critical", "Urgent")
        for c in complaints
    )
    # Metrics
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        render_portal_metric("📋", "Department Total", total_c, "All assigned", "", "blue")
    with m2:
        render_portal_metric("⏳", "Pending Review", pending_c, "Awaiting inspection", "", "orange")
    with m3:
        render_portal_metric("🚨", "Critical / Urgent", high_priority_c, "Open · priority queue", "", "red")
    with m4:
        render_portal_metric("🔧", "In Progress", in_prog_c, "Crews dispatched", "", "blue")
    with m5:
        render_portal_metric("✅", "Resolved", resolved_c, "Closed tickets", "", "green")

    st.markdown("<br>", unsafe_allow_html=True)

    # Search and Filter
    f_c1, f_c2, f_c3 = st.columns([2, 1, 1])
    with f_c1:
        sq = st.text_input("Search Department Queue", placeholder="Search by text, location, or ticket ID...")
    with f_c2:
        sf = st.selectbox("Status Filter", ["All", "pending", "seen", "in_progress", "resolved"])
    with f_c3:
        priority_filter = st.selectbox("Priority Filter", ["All", "Critical", "Urgent", "Normal"])

    filtered = complaints
    if sq:
        q = sq.lower()
        filtered = [c for c in filtered if q in c.get("description", "").lower() or q in c.get("location", "").lower()]
    if sf != "All":
        filtered = [c for c in filtered if c.get("status") == sf]
    if priority_filter != "All":
        filtered = [c for c in filtered if c.get("urgencyLevel") == priority_filter]

    st.write(f"Showing **{len(filtered)}** grievances in department queue")
    st.caption("Ordered by Critical → Urgent → Normal, then urgency score and oldest submission; resolved complaints are last.")

    if not filtered:
        st.info("No complaints matching the active filter.")
    else:
        for comp in filtered:
            render_complaint_card(comp)


# ════════════════════════════════════════════════════════════════
#  2. Action & Resolution (Status update, Notes, Evidence)
# ════════════════════════════════════════════════════════════════
def _render_action_and_resolution(dept: str):
    render_section_title("Grievance Action & Remediation Workbench", "Update investigation progress, log field notes, and upload resolution proof")

    res = api_client.get_authority_complaints(sort_by="priority")
    if not isinstance(res, list):
        detail = res.get("detail", "Unable to load department complaints.") if isinstance(res, dict) else "Unable to load department complaints."
        st.error(f"Resolution workbench unavailable: {detail}")
        return
    complaints = sort_complaints_by_priority(res)

    if not complaints:
        st.info("No complaints assigned to your department queue.")
        return

    comp_options = {
        f"#{c.get('id', '')[-6:].upper()} – {c.get('location', '')} [{c.get('status', '').upper()}]": c
        for c in complaints
    }
    sel_label = st.selectbox("Select Grievance to Remediate", list(comp_options.keys()))
    comp = comp_options[sel_label]
    cid = comp.get("id")
    current_status = comp.get("status", "pending")

    view_col, action_col = st.columns([1.3, 1], gap="large")

    with view_col:
        render_complaint_card(comp)
        render_timeline(comp)
        render_photo_compare(
            before_path=comp.get("imagePath", ""),
            after_path=comp.get("resolutionImagePath", ""),
        )

        # Existing notes
        notes = comp.get("notes", [])
        if notes:
            st.markdown("<h4 style='color: #0f172a; font-size: 0.95rem; margin-top: 1rem;'>📋 Inspection History</h4>", unsafe_allow_html=True)
            for n in notes:
                author = n.get("authorityName", "Officer")
                txt = n.get("text", "")
                t_str = str(n.get("createdAt", ""))[:16]
                st.markdown(
                    f"""
                    <div style="background: #ffffff; border-left: 3px solid #2563eb; border-radius: 6px; padding: 0.65rem 0.85rem; margin-bottom: 0.4rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
                        <div style="font-weight: 700; font-size: 0.8rem; color: #1e3a8a;">{author} · <span style="font-weight: 400; color: #94a3b8;">{t_str}</span></div>
                        <div style="font-size: 0.85rem; color: #334155; margin-top: 2px;">{txt}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with action_col:
        st.markdown(
            """
            <div class="gov-card">
                <h4 style="margin: 0 0 6px 0; color: #0a2540;">🛠️ Operational Actions</h4>
                <p style="font-size: 0.82rem; color: #64748b;">Execute status transitions or submit field remediation evidence.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── 1. Status Transition ────────────────────────────────
        st.markdown("<h5 style='color: #0f172a; margin-bottom: 4px;'>1. Status Transition</h5>", unsafe_allow_html=True)
        transitions = {
            "pending": ["seen"],
            "seen": ["in_progress"],
            "in_progress": ["resolved"],
            "resolved": [],
        }
        allowed = transitions.get(current_status, [])
        if allowed:
            next_status = st.selectbox(
                f"Next valid status (currently {current_status.replace('_', ' ').title()}):",
                allowed,
                format_func=lambda x: x.replace("_", " ").title(),
            )
            st.caption("Status changes follow the required sequence. Close a grievance with the evidence action below.")
            if st.button("Update Status", type="primary", key="btn_update_status", use_container_width=True):
                with st.spinner("Updating status..."):
                    res = api_client.update_complaint_status(cid, next_status)
                if res and not res.get("error"):
                    st.success(f"Status updated to {next_status}!")
                    st.rerun()
                else:
                    detail = res.get("detail", "Error updating status") if res else "Failed"
                    st.error(f"Error: {detail}")
        else:
            st.info(f"Grievance is currently marked as **{current_status.upper()}** (Final state).")

        st.markdown("<hr style='margin: 1rem 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)

        # ── 2. Add Field Inspection Note ────────────────────────
        st.markdown("<h5 style='color: #0f172a; margin-bottom: 4px;'>2. Log Field Inspection Note</h5>", unsafe_allow_html=True)
        note_text = st.text_area("Inspection Note", placeholder="e.g. Field crew inspected site. Replacement valve ordered.", key="add_note_txt")
        if st.button("Add Inspection Note", key="btn_add_note", use_container_width=True):
            if note_text:
                with st.spinner("Logging note in audit record..."):
                    res = api_client.add_note(cid, note_text.strip())
                if res and not res.get("error"):
                    st.success("Inspection note appended to ticket!")
                    st.rerun()
                else:
                    st.error("Failed to add note.")
            else:
                st.error("Please enter note text.")

        st.markdown("<hr style='margin: 1rem 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)

        # ── 3. Upload Resolution Evidence (Section 7 Requirement)
        st.markdown("<h5 style='color: #0f172a; margin-bottom: 4px;'>3. Upload Resolution Evidence & Mark Resolved</h5>", unsafe_allow_html=True)
        res_note = st.text_input("Resolution Summary", value="Repairs completed and site cleared by department crew.")
        evidence_file = st.file_uploader("Upload After-Work Photo Proof", type=["jpg", "png", "jpeg", "webp"], key="evidence_uploader")

        if st.button("✅ Submit Evidence & Close Grievance", type="primary", key="btn_close_evidence", use_container_width=True):
            with st.spinner("Uploading proof and closing ticket..."):
                res = api_client.upload_resolution_evidence(cid, res_note, evidence_file)
            if res and not res.get("error"):
                st.success("🎉 Resolution evidence saved and ticket marked as RESOLVED!")
                st.balloons()
                st.rerun()
            else:
                detail = res.get("detail", "Failed to upload evidence") if res else "Server error"
                st.error(f"Error: {detail}")

        # ── 4. Request Identity Reveal (if anonymous) ───────────
        if comp.get("anonymous") and comp.get("identityRequest", {}).get("status") == "none":
            st.markdown("<hr style='margin: 1rem 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
            st.markdown("<h5 style='color: #0f172a; margin-bottom: 4px;'>4. Request Identity Reveal</h5>", unsafe_allow_html=True)
            st.caption("This complaint was submitted anonymously. Request citizen identification if required for on-site premises access.")
            if st.button("Request Identity Verification", key="btn_req_identity", use_container_width=True):
                with st.spinner("Transmitting formal identity reveal request..."):
                    res = api_client.request_identity_reveal(cid)
                if res and not res.get("error"):
                    st.info("Identity reveal request dispatched to citizen.")
                    st.rerun()
                else:
                    st.error("Failed to send request.")

