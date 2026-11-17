"""
CivicSense – Citizen pages.
Submit complaints, view dashboard, manage identity requests.
"""

import streamlit as st
from frontend import api_client
from frontend.components.ui import (
    render_hero_header,
    render_complaint_card,
    render_metrics_row,
    render_section_title,
    render_note,
)


def render_citizen_dashboard():
    """Main citizen dashboard."""
    render_hero_header("Citizen Dashboard", f"Welcome back, {st.session_state.get('user_name', 'Citizen')}")

    tab1, tab2, tab3 = st.tabs(["📝 Submit Complaint", "📋 My Complaints", "🔔 Notifications"])

    with tab1:
        _submit_complaint_form()

    with tab2:
        _my_complaints()

    with tab3:
        _identity_notifications()


def _submit_complaint_form():
    """Complaint submission form with AI processing."""
    render_section_title("Submit a New Complaint")

    with st.form("complaint_form", clear_on_submit=True):
        description = st.text_area(
            "Describe your complaint",
            placeholder="Provide a detailed description of the issue (min 10 characters)...",
            height=150,
        )

        col1, col2 = st.columns(2)
        with col1:
            location = st.text_input(
                "Location",
                placeholder="e.g., Colombo, Kandy, Galle",
            )
        with col2:
            anonymous = st.checkbox("Submit anonymously", value=False)

        image = st.file_uploader(
            "Attach an image (optional)",
            type=["jpg", "jpeg", "png", "webp", "gif"],
        )

        submitted = st.form_submit_button("🚀 Submit Complaint", use_container_width=True)

    if submitted:
        if not description or len(description) < 10:
            st.error("❌ Description must be at least 10 characters.")
            return
        if not location:
            st.error("❌ Location is required.")
            return

        with st.spinner("🤖 AI is analyzing your complaint..."):
            result = api_client.submit_complaint(description, location, anonymous, image)

        if isinstance(result, dict) and result.get("error"):
            st.error(f"❌ {result.get('detail', 'Submission failed')}")
        else:
            st.success("✅ Complaint submitted successfully!")
            if isinstance(result, dict):
                st.toast(f"Category: {result.get('category')} | Urgency: {result.get('urgencyLevel')}")

                # Show AI analysis results
                st.markdown("---")
                render_section_title("AI Analysis Results")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(
                        f"""
                        <div class="metric-card">
                            <div class="metric-icon">🏷️</div>
                            <div class="metric-value" style="font-size: 1.3rem;">{result.get('category', 'N/A')}</div>
                            <div class="metric-label">Category</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with col2:
                    st.markdown(
                        f"""
                        <div class="metric-card">
                            <div class="metric-icon">🎯</div>
                            <div class="metric-value" style="font-size: 1.3rem;">{result.get('urgencyLevel', 'N/A')}</div>
                            <div class="metric-label">Urgency Level</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with col3:
                    st.markdown(
                        f"""
                        <div class="metric-card">
                            <div class="metric-icon">🏢</div>
                            <div class="metric-value" style="font-size: 1.3rem;">{result.get('assignedAuthority', 'N/A')}</div>
                            <div class="metric-label">Assigned To</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                if result.get("identityNote"):
                    st.warning(f"ℹ️ {result['identityNote']}")

                st.info(f"💡 **Summary:** {result.get('summary', '')}")


def _my_complaints():
    """Display the citizen's complaints."""
    render_section_title("My Complaints")

    with st.spinner("Loading your complaints..."):
        complaints = api_client.get_my_complaints()

    if isinstance(complaints, dict) and complaints.get("error"):
        st.error(f"❌ {complaints.get('detail', 'Failed to load')}")
        return

    if not complaints:
        st.info("📭 You haven't submitted any complaints yet.")
        return

    st.markdown(f"**{len(complaints)}** complaint(s) found")

    for comp in complaints:
        render_complaint_card(comp)

        # Show notes if any
        notes = comp.get("notes", [])
        if notes:
            with st.expander(f"📝 Authority Notes ({len(notes)})"):
                for note in notes:
                    render_note(note)

        # Upvote button
        comp_id = comp.get("id", "")
        if st.button(f"👍 Upvote ({comp.get('upvotes', 0)})", key=f"upvote_{comp_id}"):
            result = api_client.upvote_complaint(comp_id)
            if isinstance(result, dict) and not result.get("error"):
                st.toast(result.get("message", "Done"))
                st.rerun()

        st.markdown("---")


def _identity_notifications():
    """Show identity reveal requests for anonymous complaints."""
    render_section_title("Identity Reveal Requests")

    with st.spinner("Checking notifications..."):
        complaints = api_client.get_my_complaints()

    if isinstance(complaints, dict) and complaints.get("error"):
        st.error("Failed to load notifications")
        return

    pending_requests = [
        c for c in (complaints or [])
        if c.get("identityRequest", {}).get("status") == "requested"
    ]

    if not pending_requests:
        st.info("🔔 No pending identity reveal requests.")
        return

    for comp in pending_requests:
        comp_id = comp.get("id", "")
        st.markdown(
            f"""
            <div class="identity-banner">
                <p>⚠️ An authority has requested to reveal your identity for a complaint at
                <strong>{comp.get('location', 'N/A')}</strong></p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(f"*\"{comp.get('description', '')[:100]}...\"*")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Approve", key=f"approve_{comp_id}"):
                result = api_client.approve_identity(comp_id)
                if isinstance(result, dict) and not result.get("error"):
                    st.success("Identity revealed to the authority.")
                    st.rerun()
                else:
                    st.error("Failed to approve")
        with col2:
            if st.button("❌ Decline", key=f"decline_{comp_id}"):
                result = api_client.decline_identity(comp_id)
                if isinstance(result, dict) and not result.get("error"):
                    st.success("Identity reveal declined.")
                    st.rerun()
                else:
                    st.error("Failed to decline")
        st.markdown("---")
