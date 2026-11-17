"""
CivicSense – Admin pages.
System-wide analytics, user management, CSV import, community/announcement management.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from frontend import api_client
from frontend.components.ui import (
    render_hero_header,
    render_complaint_card,
    render_metrics_row,
    render_section_title,
    render_community_card,
    render_announcement_card,
)


def render_admin_dashboard():
    """Main admin dashboard."""
    render_hero_header("Admin Dashboard", "System Administration & Analytics")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Analytics", "👥 Users", "📋 All Complaints", "📁 CSV Import", "🏘️ Communities"
    ])

    with tab1:
        _system_analytics()

    with tab2:
        _user_management()

    with tab3:
        _all_complaints()

    with tab4:
        _csv_import()

    with tab5:
        _community_management()


def _system_analytics():
    """System-wide analytics with Plotly charts."""
    render_section_title("System Overview")

    with st.spinner("Loading analytics..."):
        overview = api_client.get_overview_stats()
        category_data = api_client.get_category_stats()
        location_data = api_client.get_location_stats()
        trend_data = api_client.get_trend_stats("daily")

    if isinstance(overview, dict) and overview.get("error"):
        st.error("Failed to load analytics")
        return

    # Overview metrics
    if isinstance(overview, dict):
        render_metrics_row([
            {"icon": "📋", "label": "Total Complaints", "value": overview.get("total", 0)},
            {"icon": "⏳", "label": "Pending", "value": overview.get("pending", 0)},
            {"icon": "🔧", "label": "In Progress", "value": overview.get("in_progress", 0)},
            {"icon": "✅", "label": "Resolved", "value": overview.get("resolved", 0)},
        ])

        st.markdown("<br>", unsafe_allow_html=True)

        render_metrics_row([
            {"icon": "🔴", "label": "Critical", "value": overview.get("critical", 0)},
            {"icon": "🟠", "label": "Urgent", "value": overview.get("urgent", 0)},
            {"icon": "🟢", "label": "Normal", "value": overview.get("normal", 0)},
            {"icon": "📈", "label": "Resolution Rate", "value": f"{overview.get('resolution_rate', 0)}%"},
        ])

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts row 1
    col1, col2 = st.columns(2)

    with col1:
        # Status breakdown donut
        if isinstance(overview, dict):
            labels = ["Pending", "Seen", "In Progress", "Resolved"]
            values = [
                overview.get("pending", 0),
                overview.get("seen", 0),
                overview.get("in_progress", 0),
                overview.get("resolved", 0),
            ]
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.45,
                marker=dict(colors=["#94a3b8", "#0ea5e9", "#f59e0b", "#10b981"]),
            )])
            fig.update_layout(
                title="Status Breakdown",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8"),
                title_font=dict(color="#f8fafc"),
                legend=dict(font=dict(color="#94a3b8")),
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Anonymous vs Registered
        if isinstance(overview, dict):
            fig = go.Figure(data=[go.Pie(
                labels=["Anonymous", "Registered"],
                values=[
                    overview.get("anonymous_count", 0),
                    overview.get("registered_count", 0),
                ],
                hole=0.45,
                marker=dict(colors=["#64748b", "#6366f1"]),
            )])
            fig.update_layout(
                title="Anonymous vs Registered",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8"),
                title_font=dict(color="#f8fafc"),
                legend=dict(font=dict(color="#94a3b8")),
            )
            st.plotly_chart(fig, use_container_width=True)

    # Charts row 2
    col3, col4 = st.columns(2)

    with col3:
        # Category bar chart
        if isinstance(category_data, list) and category_data:
            df = pd.DataFrame(category_data)
            fig = px.bar(
                df, x="category", y="count",
                title="Complaints by Category",
                color="category",
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8"),
                title_font=dict(color="#f8fafc"),
                showlegend=False,
                xaxis_title="",
                yaxis_title="Count",
            )
            st.plotly_chart(fig, use_container_width=True)

    with col4:
        # Location bar chart
        if isinstance(location_data, list) and location_data:
            df = pd.DataFrame(location_data)
            fig = px.bar(
                df, x="location", y="count",
                title="Complaints by Location",
                color="count",
                color_continuous_scale="Viridis",
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8"),
                title_font=dict(color="#f8fafc"),
                xaxis_title="",
                yaxis_title="Count",
            )
            st.plotly_chart(fig, use_container_width=True)

    # Trend chart
    if isinstance(trend_data, list) and trend_data:
        render_section_title("Complaint Trends")
        period = st.selectbox("Period", ["daily", "weekly", "monthly"], key="trend_period")
        if period != "daily":
            trend_data = api_client.get_trend_stats(period)

        if isinstance(trend_data, list) and trend_data:
            df = pd.DataFrame(trend_data)
            fig = px.line(
                df, x="date", y="count",
                title=f"Complaints Over Time ({period.title()})",
                markers=True,
            )
            fig.update_traces(line=dict(color="#6366f1", width=3))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8"),
                title_font=dict(color="#f8fafc"),
                xaxis_title="Date",
                yaxis_title="Complaints",
            )
            st.plotly_chart(fig, use_container_width=True)


def _user_management():
    """Manage authority users."""
    render_section_title("User Management")

    # Create authority user form
    with st.expander("➕ Create Authority User", expanded=False):
        with st.form("create_auth_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name")
                email = st.text_input("Email")
            with col2:
                password = st.text_input("Password", type="password")
                department = st.selectbox(
                    "Department",
                    [
                        "Water Board", "CEB", "RDA",
                        "Municipal Council", "Police Safety", "Disaster Management",
                    ],
                )
            if st.form_submit_button("Create Authority User", use_container_width=True):
                if name and email and password:
                    result = api_client.create_authority_user(name, email, password, department)
                    if isinstance(result, dict) and not result.get("error"):
                        st.success(f"✅ Authority user created: {email}")
                    else:
                        st.error(f"❌ {result.get('detail', 'Failed')}")

    # List users
    with st.spinner("Loading users..."):
        users = api_client.get_all_users()

    if isinstance(users, dict) and not users.get("error"):
        authorities = users.get("authorities", [])
        citizens = users.get("citizens", [])

        st.markdown(f"**Authority Users ({len(authorities)})**")
        if authorities:
            df = pd.DataFrame(authorities)
            st.dataframe(df[["name", "email", "department", "createdAt"]], use_container_width=True)

        st.markdown(f"**Citizens ({len(citizens)})**")
        if citizens:
            df = pd.DataFrame(citizens)
            st.dataframe(df[["name", "email", "createdAt"]], use_container_width=True)


def _all_complaints():
    """View all complaints system-wide."""
    render_section_title("All Complaints")

    with st.spinner("Loading..."):
        complaints = api_client.get_all_complaints_admin()

    if isinstance(complaints, dict) and complaints.get("error"):
        st.error("Failed to load complaints")
        return

    if not complaints:
        st.info("No complaints in the system.")
        return

    st.markdown(f"**{len(complaints)}** total complaint(s)")
    for comp in complaints:
        render_complaint_card(comp)


def _csv_import():
    """CSV bulk import."""
    render_section_title("Bulk CSV Import")

    st.markdown(
        """
        <div class="note-card">
            <div class="note-author">📄 CSV Format</div>
            <div class="note-text">
                Required columns: <strong>text</strong>, <strong>location</strong>, <strong>timestamp</strong><br>
                Each row will go through the full AI analysis pipeline.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader("Upload CSV file", type=["csv"])
    if uploaded:
        if st.button("🚀 Process CSV", use_container_width=True):
            with st.spinner("🤖 Processing CSV through AI pipeline..."):
                result = api_client.upload_csv(uploaded)

            if isinstance(result, dict) and not result.get("error"):
                imported = result.get("imported", 0)
                errors = result.get("errors", [])
                st.success(f"✅ Successfully imported {imported} complaint(s)")
                if errors:
                    st.warning(f"⚠️ {len(errors)} row(s) had errors:")
                    for err in errors:
                        st.markdown(f"  - Row {err['row']}: {err['message']}")
            else:
                st.error(f"❌ Import failed: {result.get('detail', 'Unknown error')}")


def _community_management():
    """Admin community and announcement management."""
    render_section_title("Community Management")

    # Create community
    with st.expander("➕ Create Community", expanded=False):
        with st.form("create_community_form"):
            comm_name = st.text_input("Community Name")
            comm_desc = st.text_area("Description", height=80)
            comm_loc = st.text_input("Location")
            if st.form_submit_button("Create Community", use_container_width=True):
                if comm_name and comm_loc:
                    result = api_client.create_community(comm_name, comm_desc, comm_loc)
                    if isinstance(result, dict) and not result.get("error"):
                        st.success("✅ Community created!")
                        st.rerun()
                    else:
                        st.error(f"❌ {result.get('detail', 'Failed')}")

    # List communities
    communities = api_client.list_communities()
    if isinstance(communities, list):
        for comm in communities:
            render_community_card(comm)
            comm_id = comm.get("id", "")

            # Post announcement
            with st.expander(f"📢 Post Announcement to {comm.get('name', '')}"):
                with st.form(f"announce_form_{comm_id}"):
                    ann_title = st.text_input("Title", key=f"ann_title_{comm_id}")
                    ann_content = st.text_area("Content", key=f"ann_content_{comm_id}", height=80)
                    if st.form_submit_button("Post Announcement"):
                        if ann_title and ann_content:
                            result = api_client.create_announcement(ann_title, ann_content, comm_id)
                            if isinstance(result, dict) and not result.get("error"):
                                st.success("📢 Announcement posted!")
                                st.rerun()
