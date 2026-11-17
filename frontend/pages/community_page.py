"""
CivicSense – Community pages.
Join/leave communities, view announcements, community feed, upvote.
"""

import streamlit as st

from frontend import api_client
from frontend.components.ui import (
    render_hero_header,
    render_community_card,
    render_announcement_card,
    render_complaint_card,
    render_section_title,
)


def render_community_page():
    """Community hub page."""
    render_hero_header("Community Hub", "Connect with your local community")

    tab1, tab2 = st.tabs(["🏘️ Communities", "📰 Feed"])

    with tab1:
        _communities_list()

    with tab2:
        _community_feed()


def _communities_list():
    """List all communities with join/leave options."""
    render_section_title("Available Communities")

    with st.spinner("Loading communities..."):
        communities = api_client.list_communities()

    if isinstance(communities, dict) and communities.get("error"):
        st.error("Failed to load communities")
        return

    if not communities:
        st.info("No communities available yet.")
        return

    user_id = st.session_state.get("user_id", "")

    for comm in communities:
        render_community_card(comm)

        comm_id = comm.get("id", "")
        members = comm.get("members", [])
        is_member = user_id in members

        col1, col2 = st.columns([1, 3])
        with col1:
            if is_member:
                if st.button("🚪 Leave", key=f"leave_{comm_id}"):
                    result = api_client.leave_community(comm_id)
                    if isinstance(result, dict) and not result.get("error"):
                        st.toast("Left community")
                        st.rerun()
            else:
                if st.button("🤝 Join", key=f"join_{comm_id}"):
                    result = api_client.join_community(comm_id)
                    if isinstance(result, dict) and not result.get("error"):
                        st.toast("Joined community!")
                        st.rerun()

        # Show announcements
        announcements = api_client.get_announcements(comm_id)
        if isinstance(announcements, list) and announcements:
            with st.expander(f"📢 Announcements ({len(announcements)})"):
                for ann in announcements:
                    render_announcement_card(ann)

        st.markdown("---")


def _community_feed():
    """Community complaint feed with upvoting."""
    render_section_title("Community Feed")

    # Select community
    communities = api_client.list_communities()
    if not isinstance(communities, list) or not communities:
        st.info("Join a community to see the feed.")
        return

    user_id = st.session_state.get("user_id", "")
    my_communities = [c for c in communities if user_id in c.get("members", [])]

    if not my_communities:
        st.info("Join a community to see its feed.")
        return

    selected = st.selectbox(
        "Select Community",
        my_communities,
        format_func=lambda c: f"{c['name']} ({c['location']})",
    )

    if selected:
        comm_id = selected.get("id", "")
        with st.spinner("Loading feed..."):
            feed = api_client.get_community_feed(comm_id)

        if isinstance(feed, dict) and feed.get("error"):
            st.error("Failed to load feed")
            return

        if not feed:
            st.info("No complaints in this community's area yet.")
            return

        st.markdown(f"**{len(feed)}** complaints in {selected.get('location', 'this area')}")

        for comp in feed:
            render_complaint_card(comp)
            comp_id = comp.get("id", "")
            if st.button(
                f"👍 Upvote ({comp.get('upvotes', 0)})",
                key=f"feed_upvote_{comp_id}",
            ):
                result = api_client.upvote_complaint(comp_id)
                if isinstance(result, dict) and not result.get("error"):
                    st.toast(result.get("message", "Done"))
                    st.rerun()
