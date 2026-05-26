import streamlit as st


def apply_sidebar_styles():
    st.markdown("""
        <style>
        /* Sidebar background */
        [data-testid="stSidebar"] {
            background: linear-gradient(160deg, #1e3a5f 0%, #16213e 100%);
        }

        /* Collapse/expand arrow button */
        [data-testid="stSidebarCollapseButton"] button {
            color: white !important;
        }
        [data-testid="stSidebarCollapseButton"] button svg {
            fill: white !important;
            stroke: white !important;
        }

        /* Arrow on the main page (expand button) */
        [data-testid="stSidebarCollapsedControl"] button {
            color: white !important;
            background-color: #1e3a5f !important;
            border-radius: 50% !important;
        }
        [data-testid="stSidebarCollapsedControl"] button svg {
            fill: white !important;
            stroke: white !important;
        }

        /* Title styling */
        .sidebar-title {
            color: #ffffff;
            font-size: 20px;
            font-weight: 700;
            padding: 10px 0 6px 0;
            letter-spacing: 0.5px;
        }

        .sidebar-subtitle {
            color: #7f9fbf;
            font-size: 11px;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin-bottom: 5px;
        }

        /* Nav buttons — default state */
        [data-testid="stSidebar"] .stButton > button {
            width: 100%;
            background-color: rgba(255,255,255,0.05);
            color: #c8d8e8;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 8px;
            padding: 11px 16px;
            font-size: 13px;
            font-weight: 500;
            text-align: left;
            margin-bottom: 6px;
            transition: all 0.2s ease;
        }

        /* Button hover */
        [data-testid="stSidebar"] .stButton > button:hover {
            background-color: rgba(99, 179, 237, 0.15) !important;
            color: #63b3ed !important;
            border-color: #63b3ed !important;
        }

        /* Button active / focused */
        [data-testid="stSidebar"] .stButton > button:focus {
            background-color: rgba(99, 179, 237, 0.2) !important;
            color: #63b3ed !important;
            border-color: #63b3ed !important;
        }

        /* Active page button — highlighted */
        .nav-btn-active > button {
            background-color: rgba(99, 179, 237, 0.25) !important;
            color: #63b3ed !important;
            border-color: #63b3ed !important;
            font-weight: 600 !important;
        }

        /* Divider */
        [data-testid="stSidebar"] hr {
            border-color: rgba(255,255,255,0.1);
            margin: 12px 0;
        }

        /* Caption / footer */
        [data-testid="stSidebar"] .stCaption {
            color: #4a6a8a !important;
            font-size: 11px;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)


# Maps each page key → (button label, session_state key)
NAV_ITEMS = [
    ("📤  Upload & Create Report", "upload"),
    ("📊  Calculate Ageing",       "calculate_ageing"),
]


def render_sidebar():
    apply_sidebar_styles()

    # Default page on first load
    if "page" not in st.session_state:
        st.session_state["page"] = "upload"

    with st.sidebar:
        st.markdown('<p class="sidebar-title">⚙️ Service Calls Ageing App</p>',
                    unsafe_allow_html=True)
        st.markdown('<p class="sidebar-subtitle">CALL AGEING CALCULATOR</p>',
                    unsafe_allow_html=True)

        st.divider()

        # ── Navigation buttons ──────────────────────────────────────────────
        for label, page_key in NAV_ITEMS:
            # Wrap in a div to apply the active highlight class when selected
            is_active = st.session_state["page"] == page_key
            if is_active:
                st.markdown('<div class="nav-btn-active">', unsafe_allow_html=True)

            if st.button(label, key=f"nav_{page_key}"):
                st.session_state["page"] = page_key

            if is_active:
                st.markdown('</div>', unsafe_allow_html=True)

        st.divider()

        st.caption("© 2025 Service App v1.0")

    return st.session_state["page"]