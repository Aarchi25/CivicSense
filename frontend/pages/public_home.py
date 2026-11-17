"""
CivicSense – Public Landing Page.
Professional government-service portal aesthetics inspired by modern civic portals.
Displays the portal introduction, service features, workflow, and account entry points.
"""

import streamlit as st
from frontend.i18n import t, render_language_selector, get_lang


def render_public_home():
    """Render the official CivicSense public portal."""

    # ── Top Government Navigation Bar ───────────────────────────
    top_col1, top_col2, top_col3 = st.columns([2.8, 2.7, 2.5])
    with top_col1:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 12px; padding: 0.2rem 0;">
                <div id="home"></div>
                <span style="font-size: 2.2rem;">🏛️</span>
                <div>
                    <h2 style="margin: 0; font-size: 1.35rem; font-weight: 800; color: #0a2540;">{t("app_title")}</h2>
                    <p style="margin: 0; font-size: 0.72rem; color: #64748b; font-weight: 600;">{t("app_tagline")}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with top_col2:
        st.markdown(
            f"""
            <nav class="gov-nav-links" aria-label="Main navigation" style="padding-top: 0.6rem;">
                <a href="#home">{t("home")}</a>
                <a href="#services">{t("services")}</a>
                <a href="#how-it-works">{t("how_it_works")}</a>
            </nav>
            """,
            unsafe_allow_html=True,
        )

    with top_col3:
        btn_c1, btn_c2, btn_c3 = st.columns([1, 1, 1.2])
        with btn_c1:
            if st.button(t("sign_in"), key="top_signin_btn", use_container_width=True):
                st.session_state["view"] = "auth"
                st.session_state["auth_tab"] = "login"
                st.rerun()
        with btn_c2:
            if st.button(t("register"), type="primary", key="top_reg_btn", use_container_width=True):
                st.session_state["view"] = "auth"
                st.session_state["auth_tab"] = "register"
                st.rerun()
        with btn_c3:
            render_language_selector()

    st.markdown("<hr style='margin: 0.5rem 0 1.25rem 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)

    # ── Main Hero Section ──────────────────────────────────────
    with st.container():
        st.markdown(
            f"""
            <div class="hero-city-card">
                <span class="hero-pill-badge" style="width: fit-content;">{t("hero_badge")}</span>
                <h2>{t("hero_title")}</h2>
                <p>{t("hero_desc")}</p>
                <div class="city-tags-row">
                    <span class="city-tag">{t("tag_nlp")}</span>
                    <span class="city-tag">{t("tag_urgency")}</span>
                    <span class="city-tag">{t("tag_anon")}</span>
                    <span class="city-tag">{t("tag_gis")}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(t("btn_lodge_grievance"), type="primary", key="hero_lodge_btn", use_container_width=True):
            st.session_state["view"] = "auth"
            st.session_state["auth_tab"] = "login"
            st.rerun()


    # ── Core System Features (Requirement 2) ───────────────────
    st.markdown(
        f"""
        <div id="services" style="margin: 2rem 0 1rem 0;">
            <h3 style="font-size: 1.4rem; font-weight: 800; color: #0a2540; text-align: center; margin-bottom: 0.3rem;">{t("features_title")}</h3>
            <p style="color: #64748b; text-align: center; font-size: 0.9rem; margin-bottom: 1.5rem;">{t("features_sub")}</p>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1.25rem;">
                <div class="gov-card">
                    <div style="font-size: 1.8rem; margin-bottom: 0.5rem;">🤖</div>
                    <h4 style="color: #0a2540; font-weight: 700; margin-bottom: 0.4rem;">{t("feat_ai_title")}</h4>
                    <p style="color: #475569; font-size: 0.88rem; line-height: 1.5;">{t("feat_ai_desc")}</p>
                </div>
                <div class="gov-card">
                    <div style="font-size: 1.8rem; margin-bottom: 0.5rem;">🎯</div>
                    <h4 style="color: #0a2540; font-weight: 700; margin-bottom: 0.4rem;">{t("feat_urgency_title")}</h4>
                    <p style="color: #475569; font-size: 0.88rem; line-height: 1.5;">{t("feat_urgency_desc")}</p>
                </div>
                <div class="gov-card">
                    <div style="font-size: 1.8rem; margin-bottom: 0.5rem;">🏢</div>
                    <h4 style="color: #0a2540; font-weight: 700; margin-bottom: 0.4rem;">{t("feat_dispatch_title")}</h4>
                    <p style="color: #475569; font-size: 0.88rem; line-height: 1.5;">{t("feat_dispatch_desc")}</p>
                </div>
                <div class="gov-card">
                    <div style="font-size: 1.8rem; margin-bottom: 0.5rem;">🔒</div>
                    <h4 style="color: #0a2540; font-weight: 700; margin-bottom: 0.4rem;">{t("feat_anon_title")}</h4>
                    <p style="color: #475569; font-size: 0.88rem; line-height: 1.5;">{t("feat_anon_desc")}</p>
                </div>
                <div class="gov-card">
                    <div style="font-size: 1.8rem; margin-bottom: 0.5rem;">📍</div>
                    <h4 style="color: #0a2540; font-weight: 700; margin-bottom: 0.4rem;">{t("feat_track_title")}</h4>
                    <p style="color: #475569; font-size: 0.88rem; line-height: 1.5;">{t("feat_track_desc")}</p>
                </div>
                <div class="gov-card">
                    <div style="font-size: 1.8rem; margin-bottom: 0.5rem;">🏘️</div>
                    <h4 style="color: #0a2540; font-weight: 700; margin-bottom: 0.4rem;">{t("feat_comm_title")}</h4>
                    <p style="color: #475569; font-size: 0.88rem; line-height: 1.5;">{t("feat_comm_desc")}</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── How It Works (4-Step Process) ───────────────────────────
    st.markdown(
        f"""
        <div id="how-it-works" class="gov-card" style="margin: 2rem 0; padding: 2rem; background: linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%);">
            <h3 style="font-size: 1.35rem; font-weight: 800; color: #0a2540; text-align: center; margin-bottom: 1.5rem;">
                {t("hiw_title")}
            </h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1.5rem;">
                <div style="text-align: center;">
                    <div style="width: 48px; height: 48px; border-radius: 50%; background: #2563eb; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; font-weight: 800; margin: 0 auto 0.75rem auto;">1</div>
                    <h5 style="color: #0f172a; margin-bottom: 0.3rem;">{t("hiw_s1_title")}</h5>
                    <p style="font-size: 0.82rem; color: #64748b;">{t("hiw_s1_desc")}</p>
                </div>
                <div style="text-align: center;">
                    <div style="width: 48px; height: 48px; border-radius: 50%; background: #0284c7; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; font-weight: 800; margin: 0 auto 0.75rem auto;">2</div>
                    <h5 style="color: #0f172a; margin-bottom: 0.3rem;">{t("hiw_s2_title")}</h5>
                    <p style="font-size: 0.82rem; color: #64748b;">{t("hiw_s2_desc")}</p>
                </div>
                <div style="text-align: center;">
                    <div style="width: 48px; height: 48px; border-radius: 50%; background: #059669; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; font-weight: 800; margin: 0 auto 0.75rem auto;">3</div>
                    <h5 style="color: #0f172a; margin-bottom: 0.3rem;">{t("hiw_s3_title")}</h5>
                    <p style="font-size: 0.82rem; color: #64748b;">{t("hiw_s3_desc")}</p>
                </div>
                <div style="text-align: center;">
                    <div style="width: 48px; height: 48px; border-radius: 50%; background: #10b981; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; font-weight: 800; margin: 0 auto 0.75rem auto;">4</div>
                    <h5 style="color: #0f172a; margin-bottom: 0.3rem;">{t("hiw_s4_title")}</h5>
                    <p style="font-size: 0.82rem; color: #64748b;">{t("hiw_s4_desc")}</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Call to Action & Footer ─────────────────────────────────
    cta_banner_col1, cta_banner_col2 = st.columns([3, 1])
    with cta_banner_col1:
        st.markdown(
            f"""
            <div id="live-dashboard" style="padding: 1rem 0;">
                <h4 style="margin: 0; color: #0a2540; font-size: 1.2rem;">{t("cta_title")}</h4>
                <p style="margin: 4px 0 0 0; color: #64748b; font-size: 0.85rem;">{t("cta_sub")}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with cta_banner_col2:
        if st.button(t("cta_btn"), type="primary", key="footer_cta_btn", use_container_width=True):
            st.session_state["view"] = "auth"
            st.session_state["auth_tab"] = "login"
            st.rerun()

    # Footer
    st.markdown(
        f"""
        <footer id="contact" style="margin-top: 3rem; padding: 2rem 0 1rem 0; border-top: 1px solid #e2e8f0; font-size: 0.82rem; color: #94a3b8; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 1rem;">
            <div>
                <b style="color: #0f172a;">{t("footer_portal")}</b><br>
                {t("footer_sub")}
            </div>
            <div>
                {t("footer_helplines")}
            </div>
            <div>
                {t("footer_rights")}
            </div>
        </footer>
        """,
        unsafe_allow_html=True,
    )
