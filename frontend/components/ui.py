"""
CivicSense – Government Portal Reusable UI Components.
Inspired by modern Indian municipal & government portals (CMC, GIS, Rail Madad).
Renders styled cards, timeline steppers, gauge meters, and status chips.
"""

from html import escape

import streamlit as st
from frontend.i18n import get_lang, translate_department


def render_gov_navbar(title: str = "CivicSense", subtitle: str = "Intelligent Civic Complaint Management System"):
    """Render top government portal branding header."""
    is_hi = get_lang() == "hi"
    badge_text = "● आधिकारिक सरकारी पोर्टल" if is_hi else "● Official Gov Portal"
    st.markdown(
        f"""
        <div class="gov-top-bar">
            <div class="gov-logo-badge">
                <span class="gov-emblem">🏛️</span>
                <div class="gov-title-group">
                    <h1>{title}</h1>
                    <p>{subtitle}</p>
                </div>
            </div>
            <div style="display: flex; gap: 8px; align-items: center;">
                <span class="badge-status status-resolved">{badge_text}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_portal_metric(icon: str, label: str, value, subtext: str = "", trend_tag: str = "", theme: str = "blue"):
    """Render a single government portal metric card (matching Image 3 & 6 GIS metrics)."""
    theme_class = f"icon-{theme}" if theme in ("blue", "green", "orange", "red") else "icon-blue"
    with st.container(border=True):
        icon_col, content_col = st.columns([1, 4])
        with icon_col:
            st.markdown(
                f'<span class="metric-icon-circle {theme_class}">{icon}</span>',
                unsafe_allow_html=True,
            )
        with content_col:
            st.markdown(f'<span class="metric-title">{label}</span>', unsafe_allow_html=True)
            st.markdown(f'<span class="metric-number">{value}</span>', unsafe_allow_html=True)
            if subtext:
                st.caption(subtext)
            if trend_tag:
                badge_class = "badge-trend-alert" if "-" in trend_tag or "alert" in trend_tag.lower() else "badge-trend-up"
                st.markdown(
                    f'<span class="{badge_class}">{trend_tag}</span>',
                    unsafe_allow_html=True,
                )


def render_service_gauge(percentage: float = 76.5, label: str = "Service Level", target: str = "Target 75%"):
    """Render a circular SVG gauge metric (matching Image 3 & 6)."""
    st.markdown(
        f"""
        <div class="gauge-metric-card">
            <div style="font-size: 0.85rem; font-weight: 700; color: #64748b; margin-bottom: 0.4rem;">{label}</div>
            <div class="gauge-circle">
                <span>{percentage:.1f}%</span>
            </div>
            <div style="font-size: 0.78rem; font-weight: 600; color: #10b981;">{target}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _urgency_badge(level: str) -> str:
    """HTML for urgency badge with bilingual support."""
    is_hi = get_lang() == "hi"
    level_lower = level.lower() if level else "normal"
    icons = {"critical": "🔴", "urgent": "🟠", "normal": "🟢"}
    icon = icons.get(level_lower, "⚪")
    hindi_labels = {"critical": "अति-गंभीर", "urgent": "जरूरी", "normal": "सामान्य"}
    display_label = hindi_labels.get(level_lower, level) if is_hi else level
    return f'<span class="badge-urgency urgency-{escape(level_lower, quote=True)}">{icon} {escape(display_label)}</span>'


def _status_badge(status: str) -> str:
    """HTML for status badge with bilingual support."""
    is_hi = get_lang() == "hi"
    st_clean = status.lower().replace(" ", "_") if status else "pending"
    icons = {"pending": "⏳", "seen": "👁️", "in_progress": "🔧", "resolved": "✅"}
    icon = icons.get(st_clean, "📋")
    hindi_status = {
        "pending": "लंबित",
        "seen": "देखी गई",
        "in_progress": "प्रगति पर",
        "resolved": "निस्तारित",
    }
    label = hindi_status.get(st_clean, st_clean.replace("_", " ").title()) if is_hi else st_clean.replace("_", " ").title()
    return f'<span class="badge-status status-{escape(st_clean, quote=True)}">{icon} {escape(label)}</span>'


def _category_badge(category: str) -> str:
    """HTML for category badge with bilingual support."""
    is_hi = get_lang() == "hi"
    icons = {
        "Water Issue": "💧",
        "Electricity Issue": "⚡",
        "Road Issue": "🛣️",
        "Garbage Issue": "🗑️",
        "Safety Hazard": "⚠️",
        "Environmental Issue": "🌿",
        "Disaster": "🌊",
    }
    hindi_cats = {
        "Water Issue": "जल आपूर्ति",
        "Electricity Issue": "बिजली",
        "Road Issue": "सड़क",
        "Garbage Issue": "कचरा व सफाई",
        "Safety Hazard": "सुरक्षा खतरा",
        "Environmental Issue": "पर्यावरण",
        "Disaster": "आपदा",
    }
    icon = icons.get(category, "📋")
    label = hindi_cats.get(category, category) if is_hi else category
    return f'<span style="background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; font-size: 0.78rem; font-weight: 700; padding: 0.25rem 0.6rem; border-radius: 9999px;">{icon} {escape(label)}</span>'


def _anonymous_badge(is_anonymous: bool) -> str:
    """HTML for anonymous/identified badge with bilingual support."""
    is_hi = get_lang() == "hi"
    if is_anonymous:
        label = "🔒 गुमनाम नागरिक" if is_hi else "🔒 Anonymous"
        return f'<span style="background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; font-size: 0.75rem; font-weight: 600; padding: 0.2rem 0.5rem; border-radius: 9999px;">{label}</span>'
    label = "👤 सत्यापित नागरिक" if is_hi else "👤 Verified Citizen"
    return f'<span style="background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; font-size: 0.75rem; font-weight: 600; padding: 0.2rem 0.5rem; border-radius: 9999px;">{label}</span>'


def sort_complaints_by_priority(complaints: list[dict]) -> list[dict]:
    """Order active complaints by urgency class, score, then oldest submission."""
    level_rank = {"critical": 0, "urgent": 1, "normal": 2}

    def priority_key(complaint: dict) -> tuple[bool, int, float, str]:
        level = str(complaint.get("urgencyLevel", "Normal")).lower()
        try:
            score = float(complaint.get("urgencyScore", 0) or 0)
        except (TypeError, ValueError):
            score = 0.0
        is_resolved = str(complaint.get("status", "")).lower() == "resolved"
        created = str(complaint.get("createdAt", ""))
        return is_resolved, level_rank.get(level, 3), -score, created

    return sorted(complaints, key=priority_key)


def render_timeline(complaint: dict):
    """Render vertical timeline tracking stepper matching Image 5 with bilingual support."""
    is_hi = get_lang() == "hi"
    status = complaint.get("status", "pending").lower()
    created = str(complaint.get("createdAt", "Just now" if not is_hi else "अभी"))[:16]
    updated = str(complaint.get("updatedAt", created))[:16]
    resolved_at = str(complaint.get("resolvedAt", ""))[:16]
    dept = complaint.get("assignedAuthority", "Municipal Authority" if not is_hi else "नगर निगम प्राधिकरण")

    # Determine step states
    s1_class = "marker-done"
    s2_class = "marker-done" if status in ("seen", "in_progress", "resolved") else "marker-active"
    s3_class = "marker-done" if status == "resolved" else ("marker-active" if status == "in_progress" else "marker-pending")
    s4_class = "marker-done" if status == "resolved" else "marker-pending"

    # Bilingual step labels
    t_s1 = "शिकायत दर्ज हुई" if is_hi else "Submitted"
    t_s1_desc = "शिकायत दर्ज और एन्क्रिप्ट की गई। एआई द्वारा प्रारंभिक वर्गीकरण पूरा हुआ।" if is_hi else "Grievance lodged and encrypted. AI assigned baseline classification."
    t_s2 = "संबंधित विभाग को प्रेषित" if is_hi else "Dispatched to Department"
    t_s2_desc = f"स्थल निरीक्षण और समाधान हेतु {dept} को आवंटित।" if is_hi else f"Assigned to {dept} for site inspection and dispatch."
    t_s3 = "कार्य प्रगति पर" if is_hi else "In Progress"
    t_s3_desc = "फील्ड इंजीनियरिंग टीम द्वारा कार्य शुरू कर दिया गया है।" if is_hi else "Field engineering crew mobilized. Work underway on premises."
    t_s4 = "निस्तारित" if is_hi else "Resolved"
    t_s4_desc = "समस्या का समाधान पूर्ण। समाधान प्रमाण और फोटो अपलोड की गई।" if is_hi else "Remediation complete. Evidence uploaded and citizen verified."
    t_pending = "लंबित" if is_hi else "Pending"
    t_awaiting = "सत्यापन की प्रतीक्षा" if is_hi else "Awaiting verification"

    st.markdown(
        f"""
        <div class="timeline-container">
            <div class="timeline-step">
                <div class="step-marker {s1_class}">✓</div>
                <div class="step-title">
                    <span>{t_s1}</span>
                    <span class="step-date">{created}</span>
                </div>
                <div class="step-desc">{t_s1_desc}</div>
            </div>
            <div class="timeline-step">
                <div class="step-marker {s2_class}">{"✓" if s2_class == "marker-done" else "2"}</div>
                <div class="step-title">
                    <span>{t_s2}</span>
                    <span class="step-date">{dept}</span>
                </div>
                <div class="step-desc">{t_s2_desc}</div>
            </div>
            <div class="timeline-step">
                <div class="step-marker {s3_class}">{"✓" if s3_class == "marker-done" else "3"}</div>
                <div class="step-title">
                    <span>{t_s3}</span>
                    <span class="step-date">{updated if status in ("in_progress", "resolved") else t_pending}</span>
                </div>
                <div class="step-desc">{t_s3_desc}</div>
            </div>
            <div class="timeline-step">
                <div class="step-marker {s4_class}">{"✓" if s4_class == "marker-done" else "4"}</div>
                <div class="step-title">
                    <span>{t_s4}</span>
                    <span class="step-date">{resolved_at if resolved_at else t_awaiting}</span>
                </div>
                <div class="step-desc">{t_s4_desc}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_ai_preview_card(preview: dict):
    """Render live AI prediction card matching Image 4."""
    cat = preview.get("category", "General Issue")
    conf = preview.get("confidence", 0.0)
    urg_score = preview.get("urgencyScore", 0.0)
    urg_level = preview.get("urgencyLevel", "Normal")
    dept = preview.get("assignedAuthority", "Municipal Council")
    summary = preview.get("summary", "")
    tips = preview.get("tips", "")

    st.markdown(
        f"""
        <div class="ai-diagnosis-card">
            <div class="ai-header-tag">
                <span>🤖</span> AI Diagnostic & Dispatch Preview
            </div>
            <div style="font-size: 0.88rem; color: #1e3a8a; margin-bottom: 0.5rem;">
                <b>Auto Summary:</b> {summary if summary else "Analysis in progress..."}
            </div>
            <div class="ai-grid-metrics">
                <div class="ai-metric-item">
                    <div class="lbl">Predicted Category</div>
                    <div class="val">{cat}</div>
                </div>
                <div class="ai-metric-item">
                    <div class="lbl">AI Confidence</div>
                    <div class="val">{conf:.0%}</div>
                </div>
                <div class="ai-metric-item">
                    <div class="lbl">Urgency Score</div>
                    <div class="val">{urg_score * 100:.0f} / 100</div>
                </div>
                <div class="ai-metric-item">
                    <div class="lbl">Urgency Level</div>
                    <div class="val">{urg_level}</div>
                </div>
                <div class="ai-metric-item">
                    <div class="lbl">Assigned Department</div>
                    <div class="val">{dept}</div>
                </div>
            </div>
            <div style="margin-top: 0.65rem; font-size: 0.8rem; color: #3b82f6; font-style: italic;">
                💡 {tips}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_complaint_card(complaint: dict, show_summary: bool = True):
    """Render a clean government portal complaint card with bilingual support."""
    is_hi = get_lang() == "hi"
    urgency = complaint.get("urgencyLevel", "Normal")
    status = complaint.get("status", "pending")
    category = complaint.get("category", "Civic Issue")
    description = str(complaint.get("description") or "")
    location = str(complaint.get("location") or ("स्थान निर्दिष्ट नहीं" if is_hi else "Not specified"))
    summary = str(complaint.get("summary") or "")
    dept = translate_department(str(complaint.get("assignedAuthority") or ""))
    anonymous = complaint.get("anonymous", False)
    created = str(complaint.get("createdAt", ""))[:16]
    
    lbl_score = "प्राथमिकता स्कोर" if is_hi else "Priority score"
    lbl_summary = "एआई सारांश:" if is_hi else "AI Summary:"

    try:
        priority_score = float(complaint.get("urgencyScore"))
    except (TypeError, ValueError):
        priority_html = ""
    else:
        priority_html = (
            '<span style="font-size: 0.75rem; color: #334155; font-weight: 600; margin-left: 4px;">'
            f"{lbl_score}: {priority_score:.2f}</span>"
        )

    desc_display = escape(description)
    summary_html = (
        f'<div style="font-size: 0.82rem; color: #4338ca; background: #e0e7ff; padding: 4px 8px; border-radius: 6px; margin: 0.4rem 0;">💡 <b>{lbl_summary}</b> {escape(summary)}</div>'
        if show_summary and summary
        else ""
    )

    card_html = (
        '<div class="gov-card"><div class="gov-card-header"><div>'
        f'<h4 style="margin: 3px 0; color: #0f172a; font-size: 1.05rem;">📍 {escape(location)}</h4>'
        f'</div><div style="display: flex; gap: 6px; align-items: center; flex-wrap: wrap;">{_urgency_badge(urgency)}'
        f'{_status_badge(status)}{priority_html}</div></div>'
        f'<p style="color: #334155; font-size: 0.9rem; line-height: 1.5; margin: 0.4rem 0; white-space: pre-wrap;">{desc_display}</p>'
        f'{summary_html}'
        '<div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-top: 0.6rem;">'
        f'{_category_badge(category)}{_anonymous_badge(anonymous)}'
        f'<span style="font-size: 0.78rem; color: #64748b;">🏢 {escape(dept)}</span>'
        f'<span style="font-size: 0.78rem; color: #94a3b8; margin-left: auto;">🕒 {escape(created)}</span>'
        '</div></div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)


def render_note(note: dict):
    """Render an authority inspection or resolution note."""
    author = note.get("authorityName", "Authority")
    text = note.get("text", "")
    created = str(note.get("createdAt", ""))[:16]

    st.markdown(
        f"""
        <div style="background: #f8fafc; border-left: 3px solid #2563eb; border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 0.5rem;">
            <div style="font-weight: 700; font-size: 0.85rem; color: #0f172a;">📝 {author} <span style="font-size: 0.75rem; color: #94a3b8; font-weight: 400; margin-left: 8px;">{created}</span></div>
            <div style="color: #334155; font-size: 0.85rem; margin-top: 3px;">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_community_card(community: dict):
    """Render community card."""
    name = community.get("name", "")
    desc = community.get("description", "")
    location = community.get("location", "")
    member_count = community.get("memberCount", len(community.get("members", [])))

    st.markdown(
        f"""
        <div class="gov-card">
            <h4 style="margin: 0 0 4px 0; color: #0f172a;">🏘️ {name}</h4>
            <p style="color: #64748b; font-size: 0.85rem; margin-bottom: 0.6rem;">{desc}</p>
            <div style="display: flex; gap: 12px; font-size: 0.8rem; color: #2563eb; font-weight: 600;">
                <span>📍 {location}</span>
                <span>👥 {member_count} Members</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_announcement_card(ann: dict):
    """Render official announcement card."""
    title = ann.get("title", "")
    content = ann.get("content", "")
    created = str(ann.get("createdAt", ""))[:10]

    st.markdown(
        f"""
        <div style="background: #fffbeb; border: 1px solid #fde68a; border-radius: 12px; padding: 1rem; margin-bottom: 0.75rem;">
            <div style="font-weight: 800; color: #b45309; font-size: 0.95rem; margin-bottom: 4px;">📢 {title}</div>
            <div style="color: #78350f; font-size: 0.85rem; line-height: 1.4;">{content}</div>
            <div style="font-size: 0.75rem; color: #d97706; margin-top: 6px;">Published: {created}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_title(title: str, subtitle: str = ""):
    """Render styled section header."""
    sub_html = f'<p style="color: #64748b; font-size: 0.85rem; margin: 2px 0 0 0;">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f"""
        <div style="margin: 1.25rem 0 0.85rem 0;">
            <h3 style="font-size: 1.25rem; font-weight: 800; color: #0a2540; margin: 0;">{title}</h3>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
