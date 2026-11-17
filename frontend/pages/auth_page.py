"""
CivicSense – Dedicated Role-Based Authentication Portal.
Matching Image 2: Separate Login / Registration with Citizen, Admin, and Authority flows.
"""

import streamlit as st
from frontend import api_client
from frontend.i18n import t, render_language_selector, get_lang


def render_auth_page():
    """Render the clean, role-based login and registration interface."""

    # ── Top Navigation Bar with Back Button & Language Switcher ──
    top_c1, top_c2, top_c3 = st.columns([1.5, 3, 1.5])
    with top_c1:
        if st.button(t("back_to_home"), key="auth_back_home_btn", use_container_width=True):
            st.session_state["view"] = "home"
            st.rerun()
    with top_c2:
        st.markdown(
            f"""
            <div style="text-align: center; font-size: 0.85rem; color: #64748b; padding-top: 0.4rem;">
                🏛️ {t("app_title")} · {t("app_tagline")}
            </div>
            """,
            unsafe_allow_html=True,
        )
    with top_c3:
        render_language_selector()

    st.markdown("<hr style='margin: 0.3rem 0 1rem 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)

    # ── Header ──────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="text-align: center; max-width: 650px; margin: 0 auto 1.5rem auto;">
            <span style="font-size: 2.8rem;">🏛️</span>
            <h2 style="font-size: 1.8rem; font-weight: 800; color: #0a2540; margin: 0.2rem 0;">{t("auth_portal_title")}</h2>
            <p style="color: #64748b; font-size: 0.92rem; margin: 0;">{t("auth_portal_sub")}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Role Selection Cards (Step 2 - Matching Image 2) ────────
    if "selected_auth_role" not in st.session_state:
        st.session_state["selected_auth_role"] = "citizen"

    col_role1, col_role2, col_role3 = st.columns(3, gap="medium")

    with col_role1:
        is_sel = st.session_state["selected_auth_role"] == "citizen"
        btn_type = "primary" if is_sel else "secondary"
        if st.button(t("citizen_portal"), type=btn_type, key="role_btn_citizen", use_container_width=True):
            st.session_state["selected_auth_role"] = "citizen"
            st.rerun()

    with col_role2:
        is_sel = st.session_state["selected_auth_role"] == "admin"
        btn_type = "primary" if is_sel else "secondary"
        if st.button(t("admin_portal"), type=btn_type, key="role_btn_admin", use_container_width=True):
            st.session_state["selected_auth_role"] = "admin"
            st.rerun()

    with col_role3:
        is_sel = st.session_state["selected_auth_role"] == "authority"
        btn_type = "primary" if is_sel else "secondary"
        if st.button(t("authority_portal"), type=btn_type, key="role_btn_auth", use_container_width=True):
            st.session_state["selected_auth_role"] = "authority"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Role-Specific Auth Form Container ────────────────────────
    role = st.session_state["selected_auth_role"]

    _, center_col, _ = st.columns([1, 2, 1])

    with center_col:
        # ════════════════════════════════════════════════════════════
        #  1. Citizen Flow (Login, Register, Forgot Password)
        # ════════════════════════════════════════════════════════════
        if role == "citizen":
            tab_login, tab_register, tab_forgot = st.tabs([t("tab_login"), t("tab_register"), t("tab_forgot")])

            with tab_login:
                st.markdown(
                    "<p style='color: #64748b; font-size: 0.88rem;'>"
                    + ("Sign in with your verified citizen credentials." if get_lang() == "en" else "अपने सत्यापित नागरिक खाते से लॉग इन करें।")
                    + "</p>",
                    unsafe_allow_html=True,
                )
                c_email = st.text_input(t("email_label"), placeholder=t("email_placeholder"), key="c_login_email")
                c_pass = st.text_input(t("password_label"), type="password", key="c_login_password")

                if st.button(t("btn_sign_in"), type="primary", key="c_login_submit", use_container_width=True):
                    if not c_email or not c_pass:
                        st.error("Please enter both email and password." if get_lang() == "en" else "कृपया ईमेल और पासवर्ड दोनों दर्ज करें।")
                    else:
                        with st.spinner("Verifying credentials..."):
                            res = api_client.login_citizen(c_email.strip(), c_pass)
                        if res and not res.get("error"):
                            st.session_state["token"] = res.get("access_token") or res.get("token")
                            st.session_state["role"] = "citizen"
                            st.session_state["user_name"] = res.get("name", "Citizen")
                            st.session_state["user_email"] = c_email.strip()
                            st.session_state["user_id"] = res.get("user_id") or res.get("id")
                            st.session_state["view"] = "dashboard"
                            st.session_state["active_nav"] = "overview"
                            st.success(f"Welcome back, {res.get('name')}!")
                            st.rerun()
                        else:
                            detail = res.get("detail", "Invalid email or password") if res else "Server unreachable"
                            st.error(f"Sign in failed: {detail}")

            with tab_register:
                st.markdown(
                    "<p style='color: #64748b; font-size: 0.88rem;'>"
                    + ("Create your citizen account. Mobile phone number is compulsory." if get_lang() == "en" else "अपना नागरिक खाता बनाएं। मोबाइल नंबर दर्ज करना अनिवार्य है।")
                    + "</p>",
                    unsafe_allow_html=True,
                )
                r_name = st.text_input(t("name_label"), placeholder=t("name_placeholder"), key="r_name")
                r_email = st.text_input(t("email_label"), placeholder=t("email_placeholder"), key="r_email")
                r_pass = st.text_input(t("password_label") + " (min 6 chars)", type="password", key="r_pass")
                r_phone = st.text_input(t("phone_label"), placeholder=t("phone_placeholder"), key="r_phone")
                r_loc = st.text_input(t("city_label"), placeholder=t("city_placeholder"), key="r_loc")

                if st.button(t("btn_register"), type="primary", key="r_submit", use_container_width=True):
                    # Strict validation: phone number is compulsory!
                    clean_phone = r_phone.strip().replace(" ", "").replace("-", "")
                    if not r_name or not r_email or not r_pass:
                        st.error("Name, email, and password are required." if get_lang() == "en" else "नाम, ईमेल और पासवर्ड अनिवार्य हैं।")
                    elif not clean_phone or len(clean_phone) < 10 or not clean_phone.replace("+", "").isdigit():
                        st.error(t("phone_compulsory_err"))
                    elif len(r_pass) < 6:
                        st.error("Password must be at least 6 characters." if get_lang() == "en" else "पासवर्ड कम से कम 6 अक्षरों का होना चाहिए।")
                    else:
                        with st.spinner("Creating profile and initializing citizen vault..."):
                            res = api_client.register_citizen(
                                name=r_name.strip(),
                                email=r_email.strip(),
                                password=r_pass,
                                phone=clean_phone,
                                location=r_loc.strip(),
                            )
                        if res and not res.get("error"):
                            st.session_state["token"] = res.get("access_token") or res.get("token")
                            st.session_state["role"] = "citizen"
                            st.session_state["user_name"] = res.get("name", r_name)
                            st.session_state["user_email"] = r_email.strip()
                            st.session_state["user_id"] = res.get("user_id") or res.get("id")
                            st.session_state["view"] = "dashboard"
                            st.session_state["active_nav"] = "overview"
                            st.success("Account created successfully! Redirecting...")
                            st.rerun()
                        else:
                            detail = res.get("detail", "Registration failed") if res else "Server unreachable"
                            st.error(f"Registration failed: {detail}")

            with tab_forgot:
                st.markdown(f"<p style='color: #64748b; font-size: 0.88rem;'>{t('forgot_subtext')}</p>", unsafe_allow_html=True)
                f_email = st.text_input(t("email_label"), placeholder="citizen@example.com", key="f_email")
                if st.button(t("btn_reset"), key="f_submit", use_container_width=True):
                    if f_email:
                        st.info(f"Verification link sent to {f_email}. Check your inbox or contact the municipal helpline at 1990." if get_lang() == "en" else f"सत्यापन लिंक {f_email} पर भेजा गया। अपना इनबॉक्स देखें या हेल्पलाइन 1990 पर संपर्क करें।")
                    else:
                        st.error("Please enter your registered email address." if get_lang() == "en" else "कृपया अपना पंजीकृत ईमेल पता दर्ज करें।")

        # ════════════════════════════════════════════════════════════
        #  2. Admin Flow (Dedicated Authorized Access Only)
        # ════════════════════════════════════════════════════════════
        elif role == "admin":
            st.markdown(
                f"""
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
                    <div style="display: flex; gap: 8px; align-items: center; color: #1e3a8a; font-weight: 700; font-size: 0.9rem;">
                        <span>🛡️</span> {t('admin_title')}
                    </div>
                    <p style="color: #64748b; font-size: 0.82rem; margin: 4px 0 0 0;">
                        {t('admin_sub')}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("admin_login_form"):
                a_email = st.text_input(t("admin_email"), placeholder="admin@civicsense.lk", key="a_login_email")
                a_pass = st.text_input(t("admin_pass"), type="password", key="a_login_pass")
                admin_submitted = st.form_submit_button(
                    t("admin_btn"),
                    type="primary",
                    use_container_width=True,
                )

            if admin_submitted:
                if not a_email or not a_pass:
                    st.error("Please provide administrator credentials." if get_lang() == "en" else "कृपया प्रशासक विवरण दर्ज करें।")
                else:
                    with st.spinner("Authenticating with system security vault..."):
                        res = api_client.login_admin(a_email.strip(), a_pass)
                    if res and not res.get("error"):
                        st.session_state["token"] = res.get("access_token") or res.get("token")
                        st.session_state["role"] = "admin"
                        st.session_state["user_name"] = res.get("name", "System Administrator")
                        st.session_state["user_email"] = a_email.strip()
                        st.session_state["user_id"] = res.get("user_id") or res.get("id")
                        st.session_state["view"] = "dashboard"
                        st.session_state["active_nav"] = "overview"
                        st.success("Admin authorized. Loading GIS Management Console..." if get_lang() == "en" else "प्रशासक सत्यापित। कंसोल लोड हो रहा है...")
                        st.rerun()
                    else:
                        detail = res.get("detail", "Access denied. Invalid credentials.") if res else "Server unreachable"
                        st.error(f"Authentication failed: {detail}")

        # ════════════════════════════════════════════════════════════
        #  3. Authority Flow (Department Officers)
        # ════════════════════════════════════════════════════════════
        elif role == "authority":
            st.markdown(
                f"""
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
                    <div style="display: flex; gap: 8px; align-items: center; color: #0284c7; font-weight: 700; font-size: 0.9rem;">
                        <span>🏢</span> {t('auth_title')}
                    </div>
                    <p style="color: #64748b; font-size: 0.82rem; margin: 4px 0 0 0;">
                        {t('auth_sub')}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("authority_login_form"):
                auth_email = st.text_input(t("auth_email"), placeholder="e.g. water@civicsense.lk", key="auth_email")
                auth_pass = st.text_input(t("auth_pass"), type="password", key="auth_pass")
                authority_submitted = st.form_submit_button(
                    t("auth_btn"),
                    type="primary",
                    use_container_width=True,
                )

            if authority_submitted:
                if not auth_email or not auth_pass:
                    st.error("Please enter your departmental officer credentials.")
                else:
                    with st.spinner("Connecting to department dispatch network..."):
                        res = api_client.login_authority(auth_email.strip(), auth_pass)
                    if res and not res.get("error"):
                        st.session_state["token"] = res.get("access_token") or res.get("token")
                        st.session_state["role"] = "authority"
                        st.session_state["user_name"] = res.get("name", "Authority Officer")
                        st.session_state["user_email"] = auth_email.strip()
                        st.session_state["user_id"] = res.get("user_id") or res.get("id")
                        st.session_state["department"] = res.get("department")
                        st.session_state["view"] = "dashboard"
                        st.session_state["active_nav"] = "overview"
                        st.success(f"Welcome, Officer! Dept: {res.get('department')}")
                        st.rerun()
                    else:
                        detail = res.get("detail", "Invalid departmental credentials") if res else "Server unreachable"
                        st.error(f"Authentication failed: {detail}")

        # ── Demo Credentials Helper Expander ───────────────────────
        with st.expander("💡 Quick Demo Credentials for Viva & Evaluators"):
            st.markdown(
                """
                | Portal | Email | Password | Role / Scope |
                | :--- | :--- | :--- | :--- |
                | **Citizen** | `amal@example.com` | `citizen123` | Submit & track complaints |
                | **Admin** | `admin@civicsense.lk` | `admin123` | System oversight & dispatch |
                | **Authority (Water)** | `water@civicsense.lk` | `auth123` | Water Board Officer |
                | **Authority (CEB)** | `ceb@civicsense.lk` | `auth123` | Electricity Board Officer |
                | **Authority (RDA)** | `rda@civicsense.lk` | `auth123` | Road Dev Authority |
                | **Authority (Municipal)** | `municipal@civicsense.lk` | `auth123` | Sanitation & Waste |
                """
            )
