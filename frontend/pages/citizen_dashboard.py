"""
CivicSense – Citizen Dashboard.
A dedicated portal with 7 sections:
1. Overview  2. Submit Complaint  3. My Complaints  4. Track Complaint
5. AI Assistant  6. Notifications  7. Profile
"""

import streamlit as st
from frontend import api_client
from frontend.i18n import t, get_lang
from frontend.components.ui import (
    render_portal_metric,
    render_complaint_card,
    render_timeline,
    render_section_title,
    render_announcement_card,
    _status_badge,
    _urgency_badge,
    _category_badge,
)


def render_citizen_dashboard():
    """Main citizen dashboard entry point."""
    user_name = st.session_state.get("user_name", "Citizen")

    # ── Top Bar with Language Selector & Logout ─────────────────
    nav_c1, nav_c2 = st.columns([3, 1])
    with nav_c1:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 0.5rem;">
                <span style="font-size: 1.8rem;">🏛️</span>
                <div>
                    <h3 style="margin: 0; color: #0a2540; font-weight: 800;">{t("app_title")} – {"Citizen Services Portal" if get_lang() == "en" else "नागरिक सेवा पोर्टल"}</h3>
                    <p style="margin: 0; font-size: 0.8rem; color: #64748b;">{"Welcome back" if get_lang() == "en" else "स्वागत है"}, <b>{user_name}</b> · {"Verified Citizen" if get_lang() == "en" else "सत्यापित नागरिक"}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with nav_c2:
        if st.button(t("sign_out"), key="c_top_logout", use_container_width=True):
            st.session_state["token"] = None
            st.session_state["role"] = None
            st.session_state["view"] = "home"
            st.rerun()

    # ── Horizontal Navigation Bar (7 Sections) ──────────────────
    nav_tabs = [
        t("tab_overview"),
        t("tab_submit"),
        t("tab_my_complaints"),
        t("tab_track"),
        t("tab_ai_assistant"),
        t("tab_notifications"),
        t("tab_profile"),
    ]

    active_tab = st.radio(
        "Navigation",
        nav_tabs,
        index=0,
        horizontal=True,
        label_visibility="collapsed",
    )

    st.markdown("<hr style='margin: 0.4rem 0 1.25rem 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)

    # ── Route Tab ───────────────────────────────────────────────
    if active_tab == t("tab_overview") or "Overview" in active_tab or "सारांश" in active_tab:
        _render_overview()
    elif active_tab == t("tab_submit") or "Submit" in active_tab or "शिकायत" in active_tab:
        _render_submit_complaint()
    elif active_tab == t("tab_my_complaints") or "My" in active_tab or "मेरी" in active_tab:
        _render_my_complaints()
    elif active_tab == t("tab_track") or "Track" in active_tab or "ट्रैक" in active_tab:
        _render_track_complaint()
    elif active_tab == t("tab_ai_assistant") or "Assistant" in active_tab or "एआई" in active_tab:
        _render_ai_assistant()
    elif active_tab == t("tab_notifications") or "Notifications" in active_tab or "सूचनाएं" in active_tab:
        _render_notifications()
    elif active_tab == t("tab_profile") or "Profile" in active_tab or "प्रोफ़ाइल" in active_tab:
        _render_profile()


# ════════════════════════════════════════════════════════════════
#  1. Overview
# ════════════════════════════════════════════════════════════════
def _render_overview():
    render_section_title(t("overview_heading"), t("overview_sub"))

    # Fetch citizen's complaints
    res = api_client.get_my_complaints()
    complaints = res if isinstance(res, list) else []

    total_count = len(complaints)
    pending_count = sum(1 for c in complaints if c.get("status") in ("pending", "seen"))
    in_prog_count = sum(1 for c in complaints if c.get("status") == "in_progress")
    resolved_count = sum(1 for c in complaints if c.get("status") == "resolved")

    # Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_portal_metric("📋", t("metric_my_complaints"), total_count, t("metric_my_sub"), "", "blue")
    with m2:
        render_portal_metric("⏳", t("metric_pending"), pending_count, t("metric_pending_sub"), "", "orange")
    with m3:
        render_portal_metric("🔧", t("metric_in_progress"), in_prog_count, t("metric_in_prog_sub"), "", "blue")
    with m4:
        render_portal_metric("✅", t("metric_resolved"), resolved_count, t("metric_resolved_sub"), "", "green")

    st.markdown("<br>", unsafe_allow_html=True)

    # Recent Activity
    render_section_title(t("recent_heading"))
    if not complaints:
        st.info(t("no_complaints_info"))
    else:
        for c in complaints[:3]:
            render_complaint_card(c, show_summary=False)


# ════════════════════════════════════════════════════════════════
#  2. Submit Complaint (Radio Category + Optional Description)
# ════════════════════════════════════════════════════════════════
def _render_submit_complaint():
    is_hi = get_lang() == "hi"

    # Megaphone notice banner
    st.markdown(
        f"""
        <div style="background: #eff6ff; border: 1.5px solid #bfdbfe; border-radius: 12px; padding: 1rem 1.25rem; margin-bottom: 1.25rem; display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 1.6rem;">📢</span>
            <div style="font-size: 0.9rem; color: #1e3a8a;">
                <b>{t("transparency_banner")}</b> {"Raise genuine issues for fast municipal redressal." if not is_hi else "त्वरित समाधान के लिए सही समस्या का चयन करें।"}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_form = st.container()

    with col_form:
        render_section_title(t("submit_heading"), t("submit_sub"))

        # Category options mapped for English & Hindi
        if is_hi:
            category_options = [
                ("💧 पानी की समस्या (Water Issue)", "Water Issue", [
                    "मुख्य पेयजल पाइपलाइन टूटी / पानी बह रहा है",
                    "दूषित / बदबूदार पानी आ रहा है",
                    "कई दिनों से पानी की सप्लाई पूरी तरह बंद है",
                    "नगर पालिका लाइन में पानी का दबाव बहुत कम है",
                    "सार्वजनिक नल टूटा हुआ है / मीटर से लीकेज",
                ]),
                ("⚡ बिजली की समस्या (Electricity Issue)", "Electricity Issue", [
                    "रात में स्ट्रीट लाइट बंद है",
                    "बार-बार बिजली कटौती / वोल्टेज में भारी उतार-चढ़ाव",
                    "ट्रांसफार्मर में स्पार्किंग / जलने की बदबू",
                    "सड़क पर खुला तार लटक रहा है (गंभीर खतरा)",
                    "बिजली का खंभा झुका या टूटा हुआ है",
                ]),
                ("🛣️ सड़क व गड्ढे की समस्या (Road Issue)", "Road Issue", [
                    "सड़क पर गहरा गड्ढा / दुर्घटना का खतरा",
                    "सड़क का डामर उखड़ा हुआ / टूटी सड़क",
                    "पैदल फुटपाथ टूटा या अवरुद्ध है",
                    "रोड डिवाइडर या स्पीड ब्रेकर टूटा हुआ",
                    "सड़क धंस गई है (गंभीर जोखिम)",
                ]),
                ("🗑️ कचरा व सफाई (Garbage & Sanitation)", "Garbage Issue", [
                    "कचरा पेटी कई दिनों से भरी पड़ी है",
                    "सड़क या खाली प्लॉट पर खुले में कचरा फेंका गया",
                    "नाली जाम है / गंदा बदबूदार पानी बह रहा है",
                    "सड़क पर मृत पशु पड़ा हुआ है",
                    "डोर-टू-डोर कचरा उठाने वाली गाड़ी नहीं आ रही",
                ]),
                ("⚠️ सुरक्षा का खतरा (Safety Hazard)", "Safety Hazard", [
                    "खुला मैनहोल / नाले का गड्ढा (दुर्घटना का खतरा)",
                    "सड़क पर पेड़ गिर गया है / रास्ता बंद",
                    "खतरनाक झुकी हुई दीवार गिरने की कगार पर",
                    "पूरी तरह अंधेरी सार्वजनिक गली / सुरक्षा जोखिम",
                    "सड़क पर मलबा / निर्माण सामग्री पड़ी है",
                ]),
                ("🌿 पर्यावरण प्रदूषण (Environmental Issue)", "Environmental Issue", [
                    "औद्योगिक कचरा या सीवेज खुले में बहाया जा रहा",
                    "जहरीला धुआं / खुले में प्लास्टिक जलाया जा रहा",
                    "ठहरा हुआ गंदा पानी / मच्छर पनप रहे",
                    "सड़क किनारे के हरे पेड़ों की अवैध कटाई",
                    "रिहायशी इलाके में भारी ध्वनि प्रदूषण",
                ]),
                ("🌊 आपदा व जलभराव (Disaster / Flooding)", "Disaster", [
                    "बारिश के बाद सड़कों पर भारी जलभराव",
                    "घरों के अंदर बाढ़ का पानी घुस रहा है",
                    "तूफान से गिरे बिजली के खंभे व पेड़",
                    "पुलिया या ड्रेनेज ढह गया है",
                    "आपातकालीन सहायता की तुरंत आवश्यकता है",
                ]),
            ]
        else:
            category_options = [
                ("💧 Water Issue", "Water Issue", [
                    "Main drinking water pipeline cracked / leaking",
                    "Contaminated / discolored water supply",
                    "Complete water outage / no water supply for days",
                    "Low water pressure in municipal line",
                    "Broken public tap or meter leakage",
                ]),
                ("⚡ Electricity Issue", "Electricity Issue", [
                    "Streetlight not working at night",
                    "Frequent power cut / severe voltage fluctuation",
                    "Transformer sparking / burning odor",
                    "Dangling open live wire on public road (Hazard)",
                    "Tilted or broken electricity pole",
                ]),
                ("🛣️ Road Issue", "Road Issue", [
                    "Deep pothole causing accidents & vehicle damage",
                    "Broken or sunken road asphalt surface",
                    "Damaged or blocked pedestrian sidewalk / footpath",
                    "Missing or broken road divider / speed breaker",
                    "Road caved in near underground pipeline",
                ]),
                ("🗑️ Garbage & Sanitation", "Garbage Issue", [
                    "Municipal garbage bin overflowing for several days",
                    "Garbage dumped openly on street / vacant plot",
                    "Clogged drainage ditch emitting foul odor",
                    "Dead animal carcass on street",
                    "Door-to-door sanitation truck not arriving",
                ]),
                ("⚠️ Safety Hazard", "Safety Hazard", [
                    "Open uncovered manhole / sewer pit (Accident risk)",
                    "Fallen tree blocking public pathway",
                    "Dilapidated leaning wall risking collapse",
                    "Completely dark public walkway / security risk",
                    "Construction debris abandoned on public road",
                ]),
                ("🌿 Environmental Issue", "Environmental Issue", [
                    "Illegal dumping of industrial chemicals or sewage",
                    "Heavy toxic smoke or open burning of plastic",
                    "Stagnant sewage water breeding mosquitoes",
                    "Illegal cutting of avenue trees",
                    "Extreme industrial noise pollution in residential area",
                ]),
                ("🌊 Disaster / Flooding", "Disaster", [
                    "Severe street waterlogging after rain",
                    "Flood water entering residential premises",
                    "Storm debris or fallen high-tension poles",
                    "Culvert or storm drain collapse",
                    "Flash flood warning / emergency assistance needed",
                ]),
            ]

        category_labels = [opt[0] for opt in category_options]
        
        # 1. Radio Button for category
        st.markdown(f"#### {t('category_radio_label')}")
        selected_cat_label = st.radio(
            "Select Category",
            category_labels,
            index=0,
            key="complaint_cat_radio",
            label_visibility="collapsed",
        )

        # Find matching category definition
        selected_tuple = next(item for item in category_options if item[0] == selected_cat_label)
        cat_system_name = selected_tuple[1]
        sub_issue_list = selected_tuple[2]

        # 2. Quick Sub-issue Radio / Selection for non-technical citizens
        st.markdown(f"#### {t('sub_issue_label')}")
        selected_sub_issue = st.radio(
            "Specific Issue Type",
            sub_issue_list,
            index=0,
            key="complaint_subissue_radio",
            label_visibility="collapsed",
        )

        # 3. Optional detailed description
        st.markdown(f"#### {t('desc_label')}")
        desc = st.text_area(
            "Issue Description",
            placeholder=t("desc_placeholder"),
            height=90,
            key="submit_desc_input",
            label_visibility="collapsed",
        )

        char_count = len(desc.strip())
        if char_count > 0:
            st.caption(f"✍️ {char_count} {t('desc_count_caption')}")
        else:
            st.caption(f"ℹ️ {t('desc_optional_caption')}")

        # Location inputs
        loc_c1, loc_c2 = st.columns(2)
        with loc_c1:
            pincode_ward = st.text_input(t("location_ward_label"), placeholder="e.g. Ward 12 / 110001", key="submit_ward")
        with loc_c2:
            street_loc = st.text_input(t("location_street_label"), placeholder="e.g. Station Road, near Main Market", key="submit_street")

        full_location = f"{street_loc}, {pincode_ward}".strip(", ")

        # Image Proof
        img_file = st.file_uploader(
            t("photo_label"),
            type=["png", "jpg", "jpeg", "webp"],
            key="submit_img_uploader",
        )

        # Whistleblower mode
        is_anon = st.checkbox(
            t("anon_label"),
            value=False,
            help=t("anon_help"),
        )

        # Live AI Preview Expander
        with st.expander(f"🔮 {t('ai_preview_title')}"):
            test_desc = desc.strip() if desc.strip() else f"{cat_system_name}: {selected_sub_issue}"
            if st.button(t("ai_preview_btn"), key="btn_run_ai_preview"):
                with st.spinner(t("citizen_ai_evaluating")):
                    preview_res = api_client.preview_complaint_ai(
                        description=test_desc,
                        category=cat_system_name,
                        anonymous=is_anon,
                    )
                if preview_res and not preview_res.get("error"):
                    p_cols = st.columns(4)
                    with p_cols[0]:
                        st.metric(t("lbl_category"), preview_res.get("category", cat_system_name))
                    with p_cols[1]:
                        st.metric(t("lbl_urgency"), preview_res.get("urgencyLevel", "Normal"))
                    with p_cols[2]:
                        st.metric(t("lbl_score"), f"{float(preview_res.get('urgencyScore', 0.5))*100:.0f}/100")
                    with p_cols[3]:
                        st.metric(t("lbl_department"), preview_res.get("assignedAuthority", "Municipal"))
                    st.caption(f"{t('lbl_category')} AI Summary: {preview_res.get('summary', '')}")
                else:
                    st.warning(t("citizen_ai_preview_failed"))

        sub_btn = st.button(t("btn_submit_complaint"), type="primary", use_container_width=True)

    # ── Handle Submission ───────────────────────────────────────
    if sub_btn:
        if not street_loc or not pincode_ward:
            st.error(t("submit_loc_err"))
        else:
            # Construct intelligent default description if user left it blank
            if desc.strip():
                final_description = f"{cat_system_name} - {selected_sub_issue}: {desc.strip()}"
            else:
                final_description = f"{cat_system_name}: {selected_sub_issue} reported near {street_loc}, {pincode_ward}."

            with st.spinner(t("citizen_submit_progress")):
                submit_res = api_client.submit_complaint(
                    description=final_description,
                    location=full_location,
                    category=cat_system_name,
                    anonymous=is_anon,
                    image=img_file,
                )

            if submit_res and not submit_res.get("error"):
                st.success(t("submit_success"))
                st.balloons()
                urgency_score = submit_res.get("urgencyScore")
                try:
                    urgency_score_display = f"{float(urgency_score) * 100:.0f}/100"
                except (TypeError, ValueError):
                    urgency_score_display = "Not available"
                confidence = submit_res.get("confidence")
                try:
                    confidence_display = f"{float(confidence) * 100:.0f}%"
                except (TypeError, ValueError):
                    confidence_display = "Not available"

                complaint_for_display = {
                    **submit_res,
                    "description": final_description,
                    "location": full_location,
                    "anonymous": is_anon,
                    "createdAt": "Just now",
                }
                render_complaint_card(complaint_for_display, show_summary=False)
                st.markdown(f"### {t('ai_summary_heading')}")
                overview_cols = st.columns(4)
                overview_items = [
                    (t("lbl_category"), submit_res.get("category", cat_system_name)),
                    (t("lbl_urgency"), submit_res.get("urgencyLevel", "Normal")),
                    (t("lbl_score"), urgency_score_display),
                    (t("lbl_department"), submit_res.get("assignedAuthority", "Municipal")),
                ]
                for column, (label, value) in zip(overview_cols, overview_items):
                    with column:
                        render_portal_metric("🤖", label, value, "", "", "blue")
                st.info(f"AI Summary: {submit_res.get('summary') or 'Grievance cataloged and prioritized.'}")
                st.caption(f"{t('lbl_confidence')}: {confidence_display}")
                render_timeline(complaint_for_display)
            else:
                detail = submit_res.get("detail", "Failed to submit grievance.") if submit_res else "Server error"
                st.error(f"Submission Error: {detail}")


# ════════════════════════════════════════════════════════════════
#  3. My Complaints
# ════════════════════════════════════════════════════════════════
def _render_my_complaints():
    is_hi = get_lang() == "hi"
    render_section_title(t("my_comp_title"), t("my_comp_sub"))

    res = api_client.get_my_complaints()
    complaints = res if isinstance(res, list) else []

    if not complaints:
        st.info(t("no_complaints_info"))
        return

    # Filter Bar
    f1, f2 = st.columns([2, 1])
    with f1:
        search_query = st.text_input(t("search_comp_placeholder"), placeholder=t("search_comp_placeholder"), label_visibility="collapsed")
    with f2:
        status_options = [t("filter_all"), "pending", "seen", "in_progress", "resolved"]
        status_filter = st.selectbox(t("status_filter_label"), status_options, label_visibility="collapsed")

    filtered = complaints
    if search_query:
        q = search_query.lower()
        filtered = [c for c in filtered if q in c.get("description", "").lower() or q in c.get("location", "").lower() or q in c.get("assignedAuthority", "").lower()]
    if status_filter != t("filter_all"):
        filtered = [c for c in filtered if c.get("status") == status_filter]

    st.write(f"{t('showing_complaints')} **{len(filtered)}** {t('of_complaints')} **{len(complaints)}** {t('complaints_suffix')}")

    for comp in filtered:
        render_complaint_card(comp, show_summary=False)


# ════════════════════════════════════════════════════════════════
#  4. Track Complaint (Matching Image 5)
# ════════════════════════════════════════════════════════════════
def _render_track_complaint():
    is_hi = get_lang() == "hi"
    render_section_title(t("track_title"), t("track_sub"))

    res = api_client.get_my_complaints()
    complaints = res if isinstance(res, list) else []

    if not complaints:
        st.info(t("no_tickets_to_track"))
        return

    # Select complaint dropdown
    options = {f"#{c.get('id', '')[-6:].upper()} – {c.get('location', '')} ({c.get('status', '').upper()})": c for c in complaints}
    selected_label = st.selectbox(t("select_ticket_label"), list(options.keys()))
    selected_comp = options[selected_label]

    cid = selected_comp.get("id")

    # Ticket Header
    st.markdown(
        f"""
        <div class="gov-card" style="margin-top: 1rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div>
                    <h3 style="margin: 0; color: #0a2540;">{t("ticket_prefix")}{cid[-8:].upper()}</h3>
                    <p style="margin: 2px 0 0 0; color: #64748b; font-size: 0.85rem;">📍 {selected_comp.get('location')}</p>
                </div>
                <div style="display: flex; gap: 8px;">
                    {_urgency_badge(selected_comp.get('urgencyLevel', 'Normal'))}
                    {_status_badge(selected_comp.get('status', 'pending'))}
                </div>
            </div>
            <div style="background: #f8fafc; border-radius: 8px; padding: 0.85rem; margin-top: 0.75rem; font-size: 0.9rem; color: #334155;">
                <b>{t("desc_prefix")}:</b> {selected_comp.get('description')}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Vertical Timeline Stepper (Matching Image 5)
    render_timeline(selected_comp)

    # Authority Notes / Log
    notes = selected_comp.get("notes", [])
    if notes:
        st.markdown(f"<h4 style='font-size: 1rem; color: #0f172a; margin-top: 1rem;'>{t('auth_notes_heading')}</h4>", unsafe_allow_html=True)
        for n in notes:
            author = n.get("authorityName", "Officer" if not is_hi else "विभागीय अधिकारी")
            txt = n.get("text", "")
            time_str = str(n.get("createdAt", ""))[:16]
            st.markdown(
                f"""
                <div style="background: #ffffff; border-left: 3px solid #2563eb; border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <div style="font-weight: 700; font-size: 0.82rem; color: #1e3a8a;">{author} · <span style="font-weight: 400; color: #94a3b8;">{time_str}</span></div>
                    <div style="font-size: 0.88rem; color: #334155; margin-top: 2px;">{txt}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Identity Reveal Request Handler (if applicable)
    ir = selected_comp.get("identityRequest", {})
    if selected_comp.get("anonymous") and ir.get("status") == "requested":
        st.warning(t("ir_banner"))
        ac1, ac2 = st.columns(2)
        with ac1:
            if st.button(t("btn_approve_id"), key=f"appr_{cid}", type="primary", use_container_width=True):
                api_client.approve_identity(cid)
                st.success("Identity revealed to assigned authority." if not is_hi else "पहचान संबंधित विभाग को प्रकट कर दी गई है।")
                st.rerun()
        with ac2:
            if st.button(t("btn_decline_id"), key=f"decl_{cid}", use_container_width=True):
                api_client.decline_identity(cid)
                st.info("Identity request declined. Anonymity preserved." if not is_hi else "अनुरोध अस्वीकार कर दिया गया। गुमनामी सुरक्षित है।")
                st.rerun()


# ════════════════════════════════════════════════════════════════
#  5. AI Assistant
# ════════════════════════════════════════════════════════════════
def _render_ai_assistant():
    is_hi = get_lang() == "hi"
    render_section_title(t("assistant_title"), t("assistant_sub"))

    st.markdown(
        f"""
        <div class="gov-card" style="background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%);">
            <h4 style="margin: 0 0 6px 0; color: #1e40af;">{t("assistant_card_title")}</h4>
            <p style="margin: 0; color: #64748b; font-size: 0.88rem;">{t("assistant_card_sub")}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    q1, q2, q3 = st.columns(3)
    preset_q = ""
    with q1:
        if st.button(t("btn_q1"), use_container_width=True):
            preset_q = "Why are power/water issues not anonymous?"
    with q2:
        if st.button(t("btn_q2"), use_container_width=True):
            preset_q = "Help me write a strong complaint"
    with q3:
        if st.button(t("btn_q3"), use_container_width=True):
            preset_q = "Which department handles streetlights?"

    user_query = st.text_input(t("ask_question_label"), value=preset_q, placeholder=t("ask_placeholder"))

    if user_query:
        uq = user_query.lower()
        if "water" in uq or "electricity" in uq or "power" in uq or "anonymous" in uq or "बिजली" in uq or "पानी" in uq or "गुमनाम" in uq:
            if is_hi:
                st.info(
                    "💡 **नियम व नीति:** पानी की पाइपलाइन मरम्मत और बिजली ग्रिड की खराबी सीधे मीटर कनेक्शन और घरेलू परिसर से जुड़ी होती है। "
                    "तकनीशियनों की सुरक्षा और गलत रिपोर्टिंग रोकने के लिए, जल बोर्ड और विद्युत बोर्ड को रखरखाव दल भेजने से पहले सत्यापित नागरिक खातों की आवश्यकता होती है।"
                )
            else:
                st.info(
                    "💡 **Rule B & C Policy:** Water pipeline repairs and electrical grid faults directly affect specific meter connections and household premises. "
                    "To ensure technician safety and avoid fraudulent outages, the National Water Board and Electricity Board require verified citizen accounts before dispatching maintenance teams."
                )
        elif "help" in uq or "write" in uq or "strong" in uq or "draft" in uq or "मदद" in uq or "लिखने" in uq:
            if is_hi:
                st.success(
                    "📝 **एक प्रभावी शिकायत दर्ज करने के महत्वपूर्ण सुझाव:**\n\n"
                    "1. **सटीक स्थान बताएं:** सड़क का नाम, लैंडमार्क या पास का मकान नंबर जरूर लिखें।\n"
                    "2. **गंभीरता बताएं:** बताएं कि क्या रिसाव जारी है, तार स्पार्क कर रहा है, या दुर्घटना का जोखिम है।\n"
                    "3. **फोटो संलग्न करें:** फील्ड इंजीनियर फोटो प्रमाण वाले मामलों को प्राथमिकता देते हैं।\n"
                    "4. **समय अवधि बताएं:** यह समस्या कितने घंटों या दिनों से बनी हुई है।"
                )
            else:
                st.success(
                    "📝 **Tips for a Highly Actionable Complaint:**\n\n"
                    "1. **Specify Exact Location:** Include street name, landmark, and nearby house number.\n"
                    "2. **Describe Severity:** Mention if there is active leakage, sparking wires, foul odor, or accident risk.\n"
                    "3. **Attach a Photo:** Field engineers prioritize tickets with visual photographic proof.\n"
                    "4. **State Duration:** Mention how many hours or days the issue has persisted."
                )
        elif "department" in uq or "streetlight" in uq or "who" in uq or "विभाग" in uq or "लाइट" in uq:
            if is_hi:
                st.info(
                    "🏢 **विभागीय अधिकार क्षेत्र:**\n\n"
                    "- **स्ट्रीट लाइट व बिजली कटौती:** विद्युत बोर्ड (CEB)\n"
                    "- **मुख्य पाइपलाइन लीकेज व सीवेज:** राष्ट्रीय जल बोर्ड (Water Board)\n"
                    "- **सड़क के गड्ढे व हाईवे:** सड़क विकास प्राधिकरण (RDA)\n"
                    "- **कचरा व सफाई:** नगर पालिका / नगर निगम (Municipal Council)\n"
                    "- **सार्वजनिक सुरक्षा व खतरे:** पुलिस सुरक्षा (Police Safety)\n"
                    "- **बाढ़ व आपदा:** आपदा प्रबंधन केंद्र (Disaster Management)"
                )
            else:
                st.info(
                    "🏢 **Department Jurisdictions:**\n\n"
                    "- **Streetlights & Power Cuts:** CEB (Electricity Board)\n"
                    "- **Main Pipeline Leaks & Sewage:** National Water Board\n"
                    "- **Potholes & Highways:** RDA (Road Development Authority)\n"
                    "- **Garbage & Sanitation:** Municipal Council\n"
                    "- **Safety & Hazards:** Police Safety\n"
                    "- **Flooding & Landslides:** Disaster Management Center"
                )
        else:
            if is_hi:
                st.info(
                    f"🤖 **'{user_query}' पर एआई मार्गदर्शन:**\n\n"
                    "हमारा पोर्टल आपकी समस्या को समझने और प्राथमिकता स्कोर (0–100) की गणना करने के लिए अत्याधुनिक एनएलपी मॉडल (DeBERTa-v3) का उपयोग करता है। "
                    "अति-गंभीर शिकायतें (>=70) विभागीय डैशबोर्ड पर तत्काल अलर्ट ट्रिगर करती हैं। आप 'शिकायत ट्रैक करें' टैब पर प्रगति देख सकते हैं।"
                )
            else:
                st.info(
                    f"🤖 **AI Guidance on '{user_query}':**\n\n"
                    "Our platform uses zero-shot natural language understanding (DeBERTa-v3) to parse your issue and calculate an urgency index (0–100). "
                    "High-urgency complaints (>=70) trigger priority alerts on departmental dashboards. You can monitor progress on the 'Track Complaint' tab."
                )


# ════════════════════════════════════════════════════════════════
#  6. Notifications
# ════════════════════════════════════════════════════════════════
def _render_notifications():
    is_hi = get_lang() == "hi"
    render_section_title(t("notif_title"), t("notif_sub"))

    res = api_client.get_my_complaints()
    complaints = res if isinstance(res, list) else []

    alerts = []
    for c in complaints:
        cid = c.get("id", "")[-6:].upper()
        status = c.get("status")
        dept = c.get("assignedAuthority")
        
        # Check notes
        for n in c.get("notes", []):
            alerts.append({
                "icon": "📝",
                "title": f"New Authority Note on #{cid}" if not is_hi else f"#{cid} पर नई विभागीय टिप्पणी",
                "body": f"[{n.get('authorityName', dept)}]: {n.get('text')}",
                "time": str(n.get("createdAt", ""))[:16],
            })
        
        # Check identity requests
        ir = c.get("identityRequest", {})
        if ir.get("status") == "requested":
            alerts.append({
                "icon": "⚠️",
                "title": f"Identity Reveal Requested on #{cid}" if not is_hi else f"#{cid} पर पहचान सत्यापन अनुरोध",
                "body": f"{dept} has requested to verify your identity. Please review under the 'Track Complaint' tab." if not is_hi else f"{dept} ने आपकी पहचान सत्यापित करने का अनुरोध किया है। कृपया 'शिकायत ट्रैक करें' में देखें।",
                "time": str(ir.get("requestedAt", ""))[:16],
            })

        # Status alert
        if status in ("in_progress", "resolved"):
            status_text = "Resolved" if status == "resolved" else "In Progress"
            if is_hi:
                status_text = "निस्तारित" if status == "resolved" else "प्रगति पर"
            alerts.append({
                "icon": "✅" if status == "resolved" else "🔧",
                "title": f"Ticket #{cid} Updated to {status_text}" if not is_hi else f"टिकट #{cid} की स्थिति: {status_text}",
                "body": f"Your complaint in {c.get('location')} is currently {status.replace('_', ' ')} by {dept}." if not is_hi else f"{c.get('location')} में आपकी शिकायत {dept} द्वारा {status_text} है।",
                "time": str(c.get("updatedAt", c.get("createdAt", "")))[:16],
            })

    if not alerts:
        st.info(t("no_notif"))
    else:
        for a in alerts:
            st.markdown(
                f"""
                <div class="gov-card" style="padding: 1rem 1.25rem; margin-bottom: 0.6rem;">
                    <div style="display: flex; gap: 10px; align-items: flex-start;">
                        <span style="font-size: 1.3rem;">{a['icon']}</span>
                        <div>
                            <div style="font-weight: 700; color: #0f172a; font-size: 0.95rem;">{a['title']}</div>
                            <div style="color: #475569; font-size: 0.85rem; margin: 2px 0;">{a['body']}</div>
                            <div style="font-size: 0.75rem; color: #94a3b8;">{a['time']}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ════════════════════════════════════════════════════════════════
#  7. Profile
# ════════════════════════════════════════════════════════════════
def _render_profile():
    is_hi = get_lang() == "hi"
    render_section_title(t("profile_title"), t("profile_sub"))

    u_name = st.session_state.get("user_name", "Citizen")
    u_email = st.session_state.get("user_email", "amal@example.com")
    u_id = st.session_state.get("user_id", "N/A")

    badge_txt = "● सत्यापित नागरिक खाता" if is_hi else "● Verified Citizen Account"

    st.markdown(
        f"""
        <div class="gov-card" style="max-width: 600px;">
            <div style="display: flex; gap: 15px; align-items: center; margin-bottom: 1.25rem;">
                <div style="width: 60px; height: 60px; border-radius: 50%; background: #2563eb; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 1.8rem; font-weight: 800;">
                    {u_name[:1].upper()}
                </div>
                <div>
                    <h3 style="margin: 0; color: #0a2540;">{u_name}</h3>
                    <p style="margin: 2px 0 0 0; color: #64748b; font-size: 0.85rem;">{u_email}</p>
                    <span class="badge-status status-resolved" style="margin-top: 4px;">{badge_txt}</span>
                </div>
            </div>
            <hr style="border: none; border-top: 1px solid #f1f5f9; margin: 1rem 0;">
            <div style="font-size: 0.88rem; color: #334155; line-height: 1.8;">
                <div><b>{t('profile_vault_id')}:</b> <code style="color: #2563eb;">{u_id}</code></div>
                <div><b>{t('profile_account_type')}:</b> {t('profile_account_val')}</div>
                <div><b>{t('profile_jurisdiction')}:</b> {t('profile_jurisdiction_val')}</div>
                <div><b>{t('profile_encryption')}:</b> {t('profile_encryption_val')}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
