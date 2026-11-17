"""
CivicSense – Department Authority Operations Portal.
Department-isolated operations for Water Board, CEB, RDA, Municipal, Police, and Disaster Management.
"""

from html import escape

import streamlit as st

from frontend import api_client
from frontend.i18n import t, translate_department
from frontend.components.ui import (
    render_portal_metric,
    render_complaint_card,
    render_timeline,
    sort_complaints_by_priority,
)


def render_authority_dashboard():
    """Main departmental officer dashboard."""
    user_name = str(st.session_state.get("user_name") or t("auth_officer_default")).strip()
    if user_name.lower() in ("none", "null"):
        user_name = t("auth_officer_default")
    department = str(st.session_state.get("department") or "").strip()
    if not department or department.lower() in ("none", "null"):
        department = user_name.rsplit(" ", 1)[0] if user_name.lower().endswith(" officer") else t("auth_department_default")
    dept = translate_department(department)

    # ── Top Bar ─────────────────────────────────────────────────
    nav_c1, nav_c2 = st.columns([3, 1])
    with nav_c1:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 0.5rem;">
                <div>
                    <h3 style="margin: 0; color: #0a2540; font-weight: 800;">{escape(t("auth_department_welcome").format(name=user_name, department=dept))}</h3>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with nav_c2:
        if st.button(t("sign_out"), key="auth_top_logout", use_container_width=True):
            st.session_state["token"] = None
            st.session_state["role"] = None
            st.session_state["view"] = "home"
            st.rerun()

    # ── Horizontal Nav Tabs ─────────────────────────────────────
    tabs = [
        t("auth_nav_queue"),
        t("auth_nav_actions"),
    ]

    active_tab = st.radio(
        t("auth_nav_queue"),
        tabs,
        index=0,
        horizontal=True,
        label_visibility="collapsed",
    )

    st.markdown("<hr style='margin: 0.4rem 0 1.25rem 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)

    # ── Route Tab ───────────────────────────────────────────────
    if active_tab == tabs[0]:
        _render_department_queue()
    elif active_tab == tabs[1]:
        _render_action_and_resolution()


# ════════════════════════════════════════════════════════════════
#  1. Department Queue
# ════════════════════════════════════════════════════════════════
def _render_department_queue():
    # Fetch complaints
    res = api_client.get_authority_complaints(sort_by="priority")
    if not isinstance(res, list):
        detail = res.get("detail") if isinstance(res, dict) else None
        st.error(f"{t('auth_queue_error')} {detail}" if detail else t("auth_queue_error"))
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
        render_portal_metric("📋", t("auth_dept_total"), total_c, t("auth_all_assigned"), "", "blue")
    with m2:
        render_portal_metric("⏳", t("auth_pending_review"), pending_c, t("auth_awaiting_insp"), "", "orange")
    with m3:
        render_portal_metric("🚨", t("auth_critical_urg"), high_priority_c, t("auth_open_priority"), "", "red")
    with m4:
        render_portal_metric("🔧", t("auth_in_prog"), in_prog_c, t("auth_crews"), "", "blue")
    with m5:
        render_portal_metric("✅", t("auth_resolved"), resolved_c, t("auth_closed"), "", "green")

    st.markdown("<br>", unsafe_allow_html=True)

    # Search and Filter
    f_c1, f_c2, f_c3 = st.columns([2, 1, 1])
    with f_c1:
        sq = st.text_input(t("auth_search_label"), placeholder=t("auth_search_ph"))
    with f_c2:
        status_options = ["All", "pending", "seen", "in_progress", "resolved"]
        sf = st.selectbox(
            t("auth_filter_status"),
            status_options,
            format_func=lambda value: t("auth_filter_all") if value == "All" else t(f"auth_status_{value}"),
        )
    with f_c3:
        priority_options = ["All", "Critical", "Urgent", "Normal"]
        priority_filter = st.selectbox(
            t("auth_filter_priority"),
            priority_options,
            format_func=lambda value: t("auth_filter_all") if value == "All" else t(f"auth_urgency_{value.lower()}"),
        )

    filtered = complaints
    if sq:
        q = sq.lower()
        filtered = [c for c in filtered if q in c.get("description", "").lower() or q in c.get("location", "").lower()]
    if sf != "All":
        filtered = [c for c in filtered if c.get("status") == sf]
    if priority_filter != "All":
        filtered = [c for c in filtered if c.get("urgencyLevel") == priority_filter]

    st.write(t("auth_queue_count").format(count=len(filtered)))
    st.caption(t("auth_queue_order"))

    if not filtered:
        st.info(t("auth_no_matching"))
    else:
        for comp in filtered:
            render_complaint_card(comp)


# ════════════════════════════════════════════════════════════════
#  2. Action & Resolution (Status update, Notes, Evidence)
# ════════════════════════════════════════════════════════════════
def _render_action_and_resolution():
    res = api_client.get_authority_complaints(sort_by="priority")
    if not isinstance(res, list):
        detail = res.get("detail") if isinstance(res, dict) else None
        st.error(f"{t('auth_workbench_error')} {detail}" if detail else t("auth_workbench_error"))
        return
    complaints = sort_complaints_by_priority(res)

    if not complaints:
        st.info(t("auth_no_complaints"))
        return

    selected_index = st.selectbox(
        t("auth_sel_grievance"),
        range(len(complaints)),
        format_func=lambda index: (
            "{} · {}".format(
                complaints[index].get("location", ""),
                t("auth_status_" + complaints[index].get("status", "pending")),
            )
        ),
    )
    comp = complaints[selected_index]
    cid = comp.get("id")
    current_status = comp.get("status", "pending")

    view_col, action_col = st.columns([1.3, 1], gap="large")

    with view_col:
        render_complaint_card(comp)
        render_timeline(comp)

        # Existing notes
        notes = comp.get("notes", [])
        if notes:
            st.markdown(
                f"<h4 style='color: #0f172a; font-size: 0.95rem; margin-top: 1rem;'>{t('auth_insp_history')}</h4>",
                unsafe_allow_html=True,
            )
            for n in notes:
                author = n.get("authorityName", t("auth_officer_default"))
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
            f"""
            <div class="gov-card">
                <h4 style="margin: 0 0 6px 0; color: #0a2540;">{t("auth_op_actions")}</h4>
                <p style="font-size: 0.82rem; color: #64748b;">{t("auth_op_actions_sub")}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── 1. Status Transition ────────────────────────────────
        st.markdown(
            f"<h5 style='color: #0f172a; margin-bottom: 4px;'>{t('auth_status_trans')}</h5>",
            unsafe_allow_html=True,
        )
        transitions = {
            "pending": ["seen"],
            "seen": ["in_progress"],
            "in_progress": ["resolved"],
            "resolved": [],
        }
        allowed = transitions.get(current_status, [])
        if allowed:
            status_options = ["seen", "in_progress", "resolved"]
            status_cols = st.columns(3)
            for next_status, status_col in zip(status_options, status_cols):
                with status_col:
                    if st.button(
                        t(f"auth_status_{next_status}"),
                        key=f"btn_status_{next_status}_{cid}",
                        disabled=next_status not in allowed,
                        use_container_width=True,
                        type="primary" if next_status in allowed else "secondary",
                    ):
                        with st.spinner(t("auth_status_saving")):
                            res = api_client.update_complaint_status(cid, next_status)
                        if res and not res.get("error"):
                            st.success(f"{t('auth_status_updated')} {t(f'auth_status_{next_status}')}!")
                            st.rerun()
                        else:
                            detail = res.get("detail", t("auth_queue_error")) if res else t("auth_queue_error")
                            st.error(f"{t('auth_error_prefix')} {detail}")
            st.caption(t("auth_status_sequence_hint"))
        else:
            st.info(t("auth_status_final"))

        st.markdown("<hr style='margin: 1rem 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)

        # ── 2. Add Field Inspection Note ────────────────────────
        st.markdown(
            f"<h5 style='color: #0f172a; margin-bottom: 4px;'>{t('auth_log_note')}</h5>",
            unsafe_allow_html=True,
        )
        note_text = st.text_area(t("auth_note_label"), placeholder=t("auth_note_placeholder"), key="add_note_txt")
        if st.button(t("auth_btn_add_note"), key="btn_add_note", use_container_width=True):
            if note_text:
                with st.spinner(t("auth_note_saving")):
                    res = api_client.add_note(cid, note_text.strip())
                if res and not res.get("error"):
                    st.success(t("auth_note_saved"))
                    st.rerun()
                else:
                    st.error(t("auth_note_failed"))
            else:
                st.error(t("auth_note_empty_error"))

        st.markdown("<hr style='margin: 1rem 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)

        # ── 3. Upload Resolution Evidence (Section 7 Requirement)
        st.markdown(
            f"<h5 style='color: #0f172a; margin-bottom: 4px;'>{t('auth_upload_evidence')}</h5>",
            unsafe_allow_html=True,
        )
        res_note = st.text_input(t("auth_res_summary"), placeholder=t("auth_resolution_placeholder"))
        evidence_file = st.file_uploader(t("auth_upload_photo"), type=["jpg", "png", "jpeg", "webp"], key="evidence_uploader")

        if st.button(t("auth_btn_close"), type="primary", key="btn_close_evidence", use_container_width=True):
            with st.spinner(t("auth_evidence_uploading")):
                res = api_client.upload_resolution_evidence(cid, res_note, evidence_file)
            if res and not res.get("error"):
                st.success(t("auth_evidence_saved"))
                st.balloons()
                st.rerun()
            else:
                detail = res.get("detail", t("auth_evidence_failed")) if res else t("auth_evidence_failed")
                st.error(f"{t('auth_error_prefix')} {detail}")

        # ── 4. Request Identity Reveal (if anonymous) ───────────
        if comp.get("anonymous") and comp.get("identityRequest", {}).get("status") == "none":
            st.markdown("<hr style='margin: 1rem 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
            st.markdown(
                f"<h5 style='color: #0f172a; margin-bottom: 4px;'>{t('auth_id_reveal')}</h5>",
                unsafe_allow_html=True,
            )
            st.caption(t("auth_identity_request_explainer"))
            if st.button(t("auth_btn_req_identity"), key="btn_req_identity", use_container_width=True):
                with st.spinner(t("auth_id_reveal")):
                    res = api_client.request_identity_reveal(cid)
                if res and not res.get("error"):
                    st.info(t("auth_identity_requested"))
                    st.rerun()
                else:
                    st.error(t("auth_identity_failed"))
