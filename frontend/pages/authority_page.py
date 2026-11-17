"""
CivicSense – Authority pages.
View department complaints, update status, add notes, request identity, analytics.
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
    render_note,
)


def render_authority_dashboard():
    """Main authority dashboard."""
    render_hero_header(
        "Authority Dashboard",
        f"Department: {st.session_state.get('user_name', 'Authority')}",
    )

    tab1, tab2 = st.tabs(["📋 Complaints", "📊 Analytics"])

    with tab1:
        _authority_complaints()

    with tab2:
        _authority_analytics()


def _authority_complaints():
    """View and manage department complaints."""
    render_section_title("Department Complaints")

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["", "pending", "seen", "in_progress", "resolved"],
            format_func=lambda x: "All Statuses" if x == "" else x.replace("_", " ").title(),
        )
    with col2:
        urgency_filter = st.selectbox(
            "Filter by Urgency",
            ["", "Critical", "Urgent", "Normal"],
            format_func=lambda x: "All Urgency Levels" if x == "" else x,
        )

    with st.spinner("Loading complaints..."):
        complaints = api_client.get_authority_complaints(status_filter, urgency_filter)

    if isinstance(complaints, dict) and complaints.get("error"):
        st.error(f"❌ {complaints.get('detail', 'Failed to load')}")
        return

    if not complaints:
        st.info("📭 No complaints matching your filters.")
        return

    # Summary metrics
    total = len(complaints)
    pending = sum(1 for c in complaints if c.get("status") == "pending")
    critical = sum(1 for c in complaints if c.get("urgencyLevel") == "Critical")
    resolved = sum(1 for c in complaints if c.get("status") == "resolved")

    render_metrics_row([
        {"icon": "📋", "label": "Total", "value": total},
        {"icon": "⏳", "label": "Pending", "value": pending},
        {"icon": "🔴", "label": "Critical", "value": critical},
        {"icon": "✅", "label": "Resolved", "value": resolved},
    ])

    st.markdown("<br>", unsafe_allow_html=True)

    # Complaint list
    for comp in complaints:
        render_complaint_card(comp)

        comp_id = comp.get("id", "")
        current_status = comp.get("status", "pending")
        is_anonymous = comp.get("anonymous", False)

        col1, col2, col3 = st.columns(3)

        # Status update
        with col1:
            transitions = {
                "pending": "seen",
                "seen": "in_progress",
                "in_progress": "resolved",
            }
            next_status = transitions.get(current_status)
            if next_status:
                label = next_status.replace("_", " ").title()
                if st.button(f"→ Mark as {label}", key=f"status_{comp_id}"):
                    result = api_client.update_complaint_status(comp_id, next_status)
                    if isinstance(result, dict) and not result.get("error"):
                        st.success(f"✅ Status updated to {label}")
                        st.rerun()
                    else:
                        st.error(f"Failed: {result.get('detail', '')}")

        # Add note
        with col2:
            note_key = f"note_input_{comp_id}"
            note_text = st.text_input("Add note", key=note_key, placeholder="Type a note...")
            if st.button("📝 Add Note", key=f"note_btn_{comp_id}"):
                if note_text:
                    result = api_client.add_note(comp_id, note_text)
                    if isinstance(result, dict) and not result.get("error"):
                        st.success("Note added!")
                        st.rerun()
                    else:
                        st.error("Failed to add note")

        # Identity request
        with col3:
            if is_anonymous and comp.get("identityRequest", {}).get("status") == "none":
                if st.button("🔓 Request Identity", key=f"reveal_{comp_id}"):
                    result = api_client.request_identity_reveal(comp_id)
                    if isinstance(result, dict) and not result.get("error"):
                        st.success("Identity request sent!")
                        st.rerun()
                    else:
                        st.error(f"Failed: {result.get('detail', '')}")
            elif is_anonymous:
                ir_status = comp.get("identityRequest", {}).get("status", "none")
                if ir_status == "requested":
                    st.info("⏳ Identity request pending")
                elif ir_status == "approved":
                    citizen_name = comp.get("citizenName", "Revealed")
                    st.success(f"👤 Identity: {citizen_name}")
                elif ir_status == "declined":
                    st.warning("❌ Identity request declined")

        # Show existing notes
        notes = comp.get("notes", [])
        if notes:
            with st.expander(f"📝 Notes ({len(notes)})"):
                for note in notes:
                    render_note(note)

        st.markdown("---")


def _authority_analytics():
    """Authority-specific analytics."""
    render_section_title("Department Analytics")

    with st.spinner("Loading analytics..."):
        complaints = api_client.get_authority_complaints()

    if isinstance(complaints, dict) and complaints.get("error"):
        st.error("Failed to load analytics")
        return

    if not complaints:
        st.info("No data available for analytics.")
        return

    df = pd.DataFrame(complaints)

    col1, col2 = st.columns(2)

    with col1:
        # Status breakdown
        if "status" in df.columns:
            status_counts = df["status"].value_counts()
            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Status Breakdown",
                color_discrete_sequence=px.colors.sequential.Tealgrn,
                hole=0.4,
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8"),
                title_font=dict(color="#f8fafc"),
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Urgency distribution
        if "urgencyLevel" in df.columns:
            urgency_counts = df["urgencyLevel"].value_counts()
            colors = {"Critical": "#ef4444", "Urgent": "#f97316", "Normal": "#10b981"}
            fig = px.bar(
                x=urgency_counts.index,
                y=urgency_counts.values,
                title="Urgency Distribution",
                color=urgency_counts.index,
                color_discrete_map=colors,
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
