"""
CivicSense – Government Administrator Console (GIS & Rail Madad Design).
Matching Image 3 & Image 6 (GIS Dashboard) and Image 7 (Smart Classification System).
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from frontend import api_client
from frontend.i18n import t, get_lang
from frontend.components.ui import (
    render_gov_navbar,
    render_portal_metric,
    render_service_gauge,
    render_complaint_card,
    render_section_title,
    render_timeline,
    render_photo_compare,
    _status_badge,
    _urgency_badge,
    _category_badge,
    sort_complaints_by_priority,
)


def render_admin_dashboard():
    """Main administrative console orchestrator."""
    admin_name = st.session_state.get("user_name", "System Administrator")

    # ── Top Bar matching GIS Header (Image 3 & 6) ───────────────
    top_c1, top_c2, top_c3 = st.columns([3, 1.2, 1])
    with top_c1:
        _sub = t("admin_console_sub")
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 0.5rem;">
                <span style="font-size: 2rem;">🛡️</span>
                <div>
                    <h3 style="margin: 0; color: #0a2540; font-weight: 800;">{t("admin_console_title")}</h3>
                    <p style="margin: 0; font-size: 0.8rem; color: #64748b;">
                        {t("welcome")} <b>{admin_name}</b> · {_sub}
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with top_c2:
        from frontend.i18n import render_language_selector
        render_language_selector()
    with top_c3:
        if st.button(t("sign_out"), key="admin_top_logout", use_container_width=True):
            st.session_state["token"] = None
            st.session_state["role"] = None
            st.session_state["view"] = "home"
            st.rerun()

    # ── Admin Navigation Tabs (GIS & Rail Madad Sections) ────────
    is_hi = get_lang() == "hi"
    tabs = [
        "📊 GIS Overview" if not is_hi else "📊 जीआईएस अवलोकन",
        "🧠 Smart Classification" if not is_hi else "🧠 स्मार्ट वर्गीकरण",
        "📋 All Complaints" if not is_hi else "📋 सभी शिकायतें",
        "🏢 Department Assignment" if not is_hi else "🏢 विभागीय आवंटन",
        "👥 Authority & Users" if not is_hi else "👥 प्राधिकरण व उपयोगकर्ता",
        "📈 Analytics & Reports" if not is_hi else "📈 विश्लेषण व रिपोर्ट",
        "📁 CSV Ingestion" if not is_hi else "📁 CSV आयात",
        "⚙️ System Settings" if not is_hi else "⚙️ सिस्टम सेटिंग्स",
    ]

    active_tab = st.radio(
        "Admin Nav",
        tabs,
        index=0,
        horizontal=True,
        label_visibility="collapsed",
    )

    st.markdown("<hr style='margin: 0.4rem 0 1.25rem 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)

    # ── Route Tab ───────────────────────────────────────────────
    if active_tab == tabs[0]:
        _render_gis_overview()
    elif active_tab == tabs[1]:
        _render_smart_classification()
    elif active_tab == tabs[2]:
        _render_all_complaints()
    elif active_tab == tabs[3]:
        _render_department_assignment()
    elif active_tab == tabs[4]:
        _render_authority_and_users()
    elif active_tab == tabs[5]:
        _render_analytics_and_reports()
    elif active_tab == tabs[6]:
        _render_csv_ingestion()
    elif active_tab == tabs[7]:
        _render_settings()


# ════════════════════════════════════════════════════════════════
#  1. GIS Overview (Matching Image 3 & Image 6)
# ════════════════════════════════════════════════════════════════
def _render_gis_overview():
    render_section_title(t("admin_gis_title"), t("admin_gis_sub"))

    all_c = api_client.get_all_complaints_admin()
    if not isinstance(all_c, list):
        detail = all_c.get("detail", "Unable to load complaint records.") if isinstance(all_c, dict) else "Unable to load complaint records."
        st.error(f"Analytics unavailable: {detail}")
        return

    total = len(all_c)
    pending = sum(c.get("status") in ("pending", "seen") for c in all_c)
    in_prog = sum(c.get("status") == "in_progress" for c in all_c)
    resolved = sum(c.get("status") == "resolved" for c in all_c)
    high_priority = sum(
        c.get("status") != "resolved" and c.get("urgencyLevel") in ("Critical", "Urgent")
        for c in all_c
    )
    rate = round(resolved / total * 100, 1) if total else 0

    # Top Row Cards matching Image 3 & 6
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        render_portal_metric("📋", t("admin_total"), total, "Live registry", "", "blue")
    with m2:
        render_portal_metric("⏳", t("admin_awaiting"), pending, "Pending or seen", "", "orange")
    with m3:
        render_portal_metric("🔄", t("admin_in_prog"), in_prog, "Live registry", "", "blue")
    with m4:
        render_portal_metric("🚨", t("admin_high_priority"), high_priority, "Critical or urgent · unresolved", "", "red")
    with m5:
        render_service_gauge(rate, t("admin_res_rate"), f"{resolved} resolved")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Live complaints charts ─────────────────────────────────
    chart_col, cat_col = st.columns([1.8, 1.2], gap="large")

    with chart_col:
        st.markdown(f"<h4 style='color: #0f172a;'>{t('admin_chart_daily')}</h4>", unsafe_allow_html=True)
        dated_records = [
            {"Date": str(c.get("createdAt", ""))[:10], "Status": c.get("status", "pending"), "Count": 1}
            for c in all_c if c.get("createdAt")
        ]
        if dated_records:
            daily_counts = pd.DataFrame(dated_records).groupby(["Date", "Status"], as_index=False)["Count"].sum()
            fig = px.line(
                daily_counts, x="Date", y="Count", color="Status", markers=True,
                color_discrete_map={
                    "pending": "#d97706", "seen": "#2563eb",
                    "in_progress": "#0284c7", "resolved": "#059669",
                },
            )
            _apply_chart_theme(fig, height=320)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No dated complaint records are available yet.")

    with cat_col:
        st.markdown(f"<h4 style='color: #0f172a;'>{t('admin_chart_cat')}</h4>", unsafe_allow_html=True)
        category_counts = pd.DataFrame(all_c)
        if not category_counts.empty and "category" in category_counts.columns:
            category_counts = category_counts["category"].fillna("Uncategorized").value_counts().rename_axis("Category").reset_index(name="Count")
            fig = px.bar(category_counts, x="Category", y="Count", color="Category", text="Count")
            fig.update_layout(showlegend=False)
            _apply_chart_theme(fig, height=320)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No complaint categories are available yet.")

    # ── Priority queue ──────────────────────────────────────────
    render_section_title(t("admin_priority_queue"), t("admin_priority_queue_sub"))
    prioritized = sort_complaints_by_priority(all_c)
    if prioritized:
        for comp in [c for c in prioritized if c.get("status") != "resolved"][:4]:
            render_complaint_card(comp)
    else:
        st.info("No complaints have been submitted.")


# ════════════════════════════════════════════════════════════════
#  2. Smart Classification (Matching Image 7 Rail Madad View)
# ════════════════════════════════════════════════════════════════
def _render_smart_classification():
    render_section_title(t("admin_smart_class_title"), t("admin_smart_class_sub"))

    all_c = api_client.get_all_complaints_admin()
    if not isinstance(all_c, list):
        detail = all_c.get("detail", "Unable to load complaint records.") if isinstance(all_c, dict) else "Unable to load complaint records."
        st.error(f"Classification queue unavailable: {detail}")
        return
    prioritized = sort_complaints_by_priority(all_c)
    unresolved = [c for c in prioritized if c.get("status") != "resolved"]
    high_priority = [c for c in unresolved if c.get("urgencyLevel") in ("Critical", "Urgent")]

    # All figures are computed from the live complaint registry.
    sm1, sm2, sm3 = st.columns(3)
    with sm1:
        render_portal_metric("📋", t("admin_reg"), len(all_c), "Live registry", "", "blue")
    with sm2:
        render_portal_metric("⏳", t("admin_open"), len(unresolved), "Awaiting resolution", "", "orange")
    with sm3:
        render_portal_metric("🚨", t("admin_critical_urg"), len(high_priority), "Open · sorted by urgency", "", "red")

    st.markdown("<br>", unsafe_allow_html=True)

    # Search and Filter bar matching Image 7
    s_col, cat_col, stat_col, urgency_col = st.columns([2.3, 1.2, 1.2, 1.2])
    with s_col:
        search_kw = st.text_input("Search complaints...", placeholder="Search keywords, ID, or location...")
    with cat_col:
        cat_sel = st.selectbox("Category", ["All Categories", "Water Issue", "Electricity Issue", "Road Issue", "Garbage Issue", "Safety Hazard", "Environmental Issue", "Disaster"])
    with stat_col:
        stat_sel = st.selectbox("Status", ["All Status", "pending", "seen", "in_progress", "resolved"])
    with urgency_col:
        urgency_sel = st.selectbox("Priority", ["All Priorities", "Critical", "Urgent", "Normal"])

    filtered = prioritized
    if search_kw:
        sk = search_kw.lower()
        filtered = [c for c in filtered if sk in c.get("description", "").lower() or sk in c.get("location", "").lower()]
    if cat_sel != "All Categories":
        filtered = [c for c in filtered if c.get("category") == cat_sel]
    if stat_sel != "All Status":
        filtered = [c for c in filtered if c.get("status") == stat_sel]
    if urgency_sel != "All Priorities":
        filtered = [c for c in filtered if c.get("urgencyLevel") == urgency_sel]

    st.caption("Priority order: unresolved before resolved, then Critical → Urgent → Normal, highest score first, oldest first for ties.")
    st.write(f"Showing **{len(filtered)}** of **{len(all_c)}** complaints")
    # Data Table matching Image 7
    st.markdown(
        """
        <div class="table-complaint-row table-complaint-header">
            <div>ID</div>
            <div>COMPLAINT TEXT</div>
            <div>CATEGORY</div>
            <div>CONFIDENCE</div>
            <div>TIMESTAMP</div>
            <div>STATUS</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for c in filtered:
        cid_short = f"#{c.get('id', '')[-6:].upper()}"
        desc_short = c.get("description", "")[:65] + "..." if len(c.get("description", "")) > 65 else c.get("description", "")
        urg = c.get("urgencyLevel", "Normal")
        try:
            priority_score = float(c.get("urgencyScore", 0) or 0)
        except (TypeError, ValueError):
            priority_score = 0.0
        cat = c.get("category", "General")
        conf_pct = int(c.get("confidence", 0.8) * 100)
        time_str = str(c.get("createdAt", ""))[:16]
        stat = c.get("status", "pending")

        urg_tag = f"<span class='badge-urgency urgency-{urg.lower()}' style='margin-left: 6px;'>{urg}</span>"

        st.markdown(
            f"""
            <div class="table-complaint-row">
                <div style="font-weight: 700; color: #1d4ed8;">{cid_short}</div>
                <div>
                    <div style="font-weight: 600; color: #0f172a;">{desc_short}</div>
                    <div>{urg_tag} <span style="font-size: 0.75rem; color: #334155;">Score {priority_score:.2f}</span></div>
                </div>
                <div>{_category_badge(cat)}</div>
                <div>
                    <span style="font-weight: 700; font-size: 0.8rem;">{conf_pct}%</span>
                    <div class="conf-bar-wrapper">
                        <div class="conf-bar-fill" style="width: {conf_pct}%;"></div>
                    </div>
                </div>
                <div style="color: #64748b; font-size: 0.78rem;">{time_str}</div>
                <div>{_status_badge(stat)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ════════════════════════════════════════════════════════════════
#  3. All Complaints (Management & Inspector)
# ════════════════════════════════════════════════════════════════
def _render_all_complaints():
    render_section_title("Grievance Master Registry", "Complete oversight of all lodged municipal issues with inspection tools")

    all_c = api_client.get_all_complaints_admin(sort_by="priority")
    if not isinstance(all_c, list):
        detail = all_c.get("detail", "Unable to load complaint records.") if isinstance(all_c, dict) else "Unable to load complaint records."
        st.error(f"Complaint registry unavailable: {detail}")
        return
    complaints = sort_complaints_by_priority(all_c)

    if not complaints:
        st.info("No complaints found.")
        return

    st.write(f"Total Registry Records: **{len(complaints)}**")

    for comp in complaints:
        with st.expander(f"📍 {comp.get('location')} | #{comp.get('id', '')[-6:].upper()} | {comp.get('assignedAuthority')} [{comp.get('status', '').upper()}]"):
            render_complaint_card(comp)
            render_timeline(comp)
            render_photo_compare(comp.get("imagePath", ""), comp.get("resolutionImagePath", ""))


# ════════════════════════════════════════════════════════════════
#  4. Department Assignment (Section 6 Requirement)
# ════════════════════════════════════════════════════════════════
def _render_department_assignment():
    render_section_title("Department Assignment & Dispatch", "Review AI routing and reassign complaints to appropriate municipal departments")

    all_c = api_client.get_all_complaints_admin(sort_by="priority")
    if not isinstance(all_c, list):
        detail = all_c.get("detail", "Unable to load complaint records.") if isinstance(all_c, dict) else "Unable to load complaint records."
        st.error(f"Department assignment unavailable: {detail}")
        return
    complaints = all_c

    if not complaints:
        st.info("No complaints to reassign.")
        return

    complaints = sort_complaints_by_priority(complaints)
    comp_options = {}
    for c in complaints:
        try:
            priority_score = float(c.get("urgencyScore", 0) or 0)
        except (TypeError, ValueError):
            priority_score = 0.0
        label = (
            f"{c.get('urgencyLevel', 'Normal')} · {priority_score:.2f} · "
            f"#{c.get('id', '')[-6:].upper()} – {c.get('description', '')[:50]}... "
            f"(Currently: {c.get('assignedAuthority')})"
        )
        comp_options[label] = c
    selected_label = st.selectbox("Select Grievance to Inspect / Reassign", list(comp_options.keys()))
    comp = comp_options[selected_label]
    cid = comp.get("id")

    col_view, col_action = st.columns([1.5, 1], gap="large")

    with col_view:
        render_complaint_card(comp)
        st.markdown(
            f"""
            <div class="gov-card">
                <h4 style="margin: 0 0 6px 0; color: #0a2540;">🤖 AI Diagnostic Breakdown</h4>
                <div style="font-size: 0.88rem; color: #334155;">
                    <div><b>Predicted Category:</b> {comp.get('category')} (Confidence: {comp.get('confidence', 0):.0%})</div>
                    <div><b>Computed Urgency:</b> {comp.get('urgencyLevel')} (Score: {comp.get('urgencyScore', 0):.2f})</div>
                    <div><b>Sentiment Polarity:</b> {comp.get('sentiment', 0):.2f}</div>
                    <div><b>Summary:</b> {comp.get('summary')}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_action:
        st.markdown(
            """
            <div class="gov-card">
                <h4 style="margin: 0 0 6px 0; color: #0a2540;">🏢 Reassign Department</h4>
                <p style="font-size: 0.82rem; color: #64748b;">Override automated AI dispatch and reroute to a different municipal authority.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        departments = [
            "Water Board",
            "CEB",
            "RDA",
            "Municipal Council",
            "Police Safety",
            "Disaster Management",
        ]
        curr_dept = comp.get("assignedAuthority", departments[0])
        curr_idx = departments.index(curr_dept) if curr_dept in departments else 0

        new_dept = st.selectbox("Assign to Department", departments, index=curr_idx)

        if st.button("Confirm Reassignment", type="primary", use_container_width=True):
            with st.spinner("Updating central dispatch registry..."):
                res = api_client.reassign_complaint(cid, new_dept)
            if res and not res.get("error"):
                st.success(f"Grievance successfully reassigned to {new_dept}!")
                st.rerun()
            else:
                st.error("Failed to reassign department.")


# ════════════════════════════════════════════════════════════════
#  5. Authority & User Management
# ════════════════════════════════════════════════════════════════
def _render_authority_and_users():
    render_section_title("Authority Officers & Citizen Directory", "Manage departmental officer accounts and view registered citizens")

    tab_auth, tab_cit, tab_create = st.tabs(["🏢 Department Officers", "👤 Registered Citizens", "➕ Create Authority Officer"])

    with tab_auth:
        res = api_client.get_all_users()
        authorities = res.get("authorities", []) if res and not res.get("error") else []
        if authorities:
            st.dataframe(pd.DataFrame(authorities)[["name", "email", "department", "role", "createdAt"]], use_container_width=True)
        else:
            st.info("No authority officers provisioned yet.")

    with tab_cit:
        res = api_client.get_all_users()
        citizens = res.get("citizens", []) if res and not res.get("error") else []
        if citizens:
            st.dataframe(pd.DataFrame(citizens)[["name", "email", "role", "createdAt"]], use_container_width=True)
        else:
            st.info("No registered citizens found.")

    with tab_create:
        st.markdown("<h4 style='color: #0a2540;'>Provision New Department Officer Account</h4>", unsafe_allow_html=True)
        a_name = st.text_input("Officer Full Name", placeholder="e.g. Eng. Sunil Bandara")
        a_email = st.text_input("Official Email", placeholder="e.g. sunil.water@civicsense.lk")
        a_pass = st.text_input("Initial Password", type="password")
        a_dept = st.selectbox(
            "Designated Department",
            ["Water Board", "CEB", "RDA", "Municipal Council", "Police Safety", "Disaster Management"]
        )

        if st.button("Create Officer Account", type="primary", use_container_width=True):
            if not a_name or not a_email or not a_pass:
                st.error("All fields are required.")
            else:
                with st.spinner("Provisioning credentials in authority vault..."):
                    res = api_client.create_authority_user(a_name, a_email, a_pass, a_dept)
                if res and not res.get("error"):
                    st.success(f"Authority user created for {a_name} ({a_dept})!")
                    st.rerun()
                else:
                    detail = res.get("detail", "Error creating user") if res else "Server error"
                    st.error(f"Failed: {detail}")


# ════════════════════════════════════════════════════════════════
#  6. Analytics & Reports
# ════════════════════════════════════════════════════════════════
def _render_analytics_and_reports():
    render_section_title("System Analytics & Governance Reports", "Plotly intelligence charts and data export capabilities")

    all_c = api_client.get_all_complaints_admin()
    if not isinstance(all_c, list):
        detail = all_c.get("detail", "Unable to load complaint records.") if isinstance(all_c, dict) else "Unable to load complaint records."
        st.error(f"Reports unavailable: {detail}")
        return
    complaints = all_c

    if not complaints:
        st.info("No complaints have been submitted, so there is no analytics data yet.")
        return

    df = pd.DataFrame(complaints)

    c1, c2 = st.columns(2)
    with c1:
        if "category" in df.columns:
            cat_counts = df["category"].value_counts().reset_index()
            cat_counts.columns = ["Category", "Count"]
            fig_cat = px.bar(cat_counts, x="Category", y="Count", color="Category", title="Complaints by Category", text="Count")
            fig_cat.update_layout(showlegend=False)
            _apply_chart_theme(fig_cat)
            st.plotly_chart(fig_cat, use_container_width=True)

    with c2:
        if "urgencyLevel" in df.columns:
            urg_counts = df["urgencyLevel"].value_counts().reset_index()
            urg_counts.columns = ["Urgency", "Count"]
            fig_urg = px.pie(urg_counts, names="Urgency", values="Count", title="Urgency Distribution", hole=0.45,
                             color_discrete_map={"Critical": "#ef4444", "Urgent": "#f59e0b", "Normal": "#10b981"})
            _apply_chart_theme(fig_urg)
            st.plotly_chart(fig_urg, use_container_width=True)

    # Export Reports
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h4 style='color: #0a2540;'>📥 Export Governance Reports</h4>", unsafe_allow_html=True)
    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Complaints Registry CSV",
        data=csv_data,
        file_name=f"civicsense_complaints_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True,
    )


def _apply_chart_theme(fig, height: int = 320) -> None:
    """Keep Plotly titles, axes, ticks, and legends readable on light cards."""
    fig.update_layout(
        template="plotly_white",
        height=height,
        font={"color": "#334155"},
        title_font={"color": "#0f172a"},
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        legend={"font": {"color": "#334155"}},
    )
    fig.update_xaxes(
        title_font={"color": "#334155"},
        tickfont={"color": "#334155"},
        gridcolor="#e2e8f0",
    )
    fig.update_yaxes(
        title_font={"color": "#334155"},
        tickfont={"color": "#334155"},
        gridcolor="#e2e8f0",
    )


# ════════════════════════════════════════════════════════════════
#  7. CSV Ingestion
# ════════════════════════════════════════════════════════════════
def _render_csv_ingestion():
    render_section_title("Bulk CSV Complaint Ingestion", "Upload historical complaint spreadsheets for batch NLP categorization and dispatch")

    st.markdown(
        """
        <div class="gov-card">
            <h4 style="margin: 0 0 6px 0; color: #0a2540;">CSV Ingestion Format Requirements</h4>
            <p style="font-size: 0.85rem; color: #475569; margin: 0;">
                The CSV file must contain a <code>description</code> and <code>location</code> column. 
                Optional columns include <code>anonymous</code> (true/false) and <code>reported_at</code> (ISO datetime).
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    csv_file = st.file_uploader("Select Complaint CSV File", type=["csv"], key="admin_csv_uploader")

    if csv_file and st.button("Process & Ingest CSV via AI Pipeline", type="primary", use_container_width=True):
        with st.spinner("Ingesting rows, executing zero-shot classification, and routing complaints..."):
            res = api_client.upload_csv(csv_file)
        if res and not res.get("error"):
            st.success(f"✅ Ingestion Complete! Successfully processed: {res.get('processed', 0)} rows. Errors: {res.get('errors', 0)}")
        else:
            detail = res.get("detail", "CSV processing failed") if res else "Server error"
            st.error(f"Error: {detail}")


# ════════════════════════════════════════════════════════════════
#  8. System Settings
# ════════════════════════════════════════════════════════════════
def _render_settings():
    render_section_title("System Settings & Community Governance", "Configure portal endpoints, manage neighborhoods, and broadcast announcements")

    set_tab1, set_tab2 = st.tabs(["📢 Publish Public Announcement", "⚙️ Portal Configuration"])

    with set_tab1:
        st.markdown("<h4 style='color: #0a2540;'>Broadcast Official Announcement</h4>", unsafe_allow_html=True)
        ann_title = st.text_input("Announcement Title", placeholder="e.g. Pre-Monsoon Drainage Cleaning Notice")
        ann_content = st.text_area("Detailed Content", placeholder="Enter announcement body text...")

        comms = api_client.list_communities()
        if comms and not comms.get("error") and len(comms) > 0:
            comm_map = {c["name"]: c["id"] for c in comms}
            sel_comm = st.selectbox("Target Community", list(comm_map.keys()))

            if st.button("Broadcast Announcement", type="primary", use_container_width=True):
                if ann_title and ann_content:
                    res = api_client.create_announcement(ann_title, ann_content, comm_map[sel_comm])
                    if res and not res.get("error"):
                        st.success("Announcement successfully broadcast to community hub!")
                    else:
                        st.error("Failed to broadcast announcement.")
                else:
                    st.error("Please provide both title and content.")

    with set_tab2:
        st.markdown(
            """
            <div class="gov-card">
                <h4 style="margin: 0 0 8px 0; color: #0a2540;">Security & Backend Link</h4>
                <div style="font-size: 0.88rem; color: #334155; line-height: 1.8;">
                    <div><b>Active API Gateway:</b> <code>http://localhost:8000</code></div>
                    <div><b>Database Connection:</b> <code>mongodb://localhost:27017/civicsense</code></div>
                    <div><b>Classification Engine:</b> HuggingFace DeBERTa-v3 + Keyword Rule Fallback</div>
                    <div><b>Access Token Lifetime:</b> 1440 Minutes (24 Hours)</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
