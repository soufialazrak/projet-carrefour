import streamlit as st
from PIL import Image
from textwrap import dedent


def apply_global_styles():
    st.markdown(dedent("""
    <style>
    .title {
        color: #0046AD;
        text-align: center;
        font-size: 72px;
        font-weight: 800;
        margin-top: 0px;
        margin-bottom: 8px;
    }

    .subtitle {
        text-align: center;
        font-size: 24px;
        color: #4a4a4a;
        margin-bottom: 25px;
    }

    .center-text {
        text-align: center;
        font-size: 24px;
        line-height: 1.8;
        color: #1f2a44;
    }

    .small-note {
        text-align: left;
        font-size: 18px;
        margin-top: 25px;
        color: #555;
        font-style: italic;
    }

    .main-box {
        background-color: #f7f7f7;
        padding: 40px 35px;
        border-radius: 14px;
        border: 1px solid #e6e6e6;
    }

    section[data-testid="stSidebar"] {
        background-color: #f7f7f7;
        border-right: 1px solid #e6e6e6;
    }

    /* Masquer complètement la navigation native Streamlit */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }

    [data-testid="stSidebarNavItems"] {
        display: none !important;
    }

    [data-testid="stSidebarHeader"] {
        display: none !important;
    }

    div.stButton > button {
        width: 100%;
        text-align: left;
        font-size: 18px;
        padding: 0.7rem 1rem;
        border-radius: 8px;
        margin-bottom: 0.6rem;
        border: 1px solid #d9d9d9;
        background-color: white;
        color: #1f2a44;
    }

    div.stButton > button:hover {
        border-color: #0046AD;
        color: #0046AD;
    }

    .active-link {
        background: #e8f0ff;
        padding: 10px;
        border-left: 5px solid #0046AD;
        border-radius: 8px;
        font-weight: 700;
        color: #0046AD;
        margin-bottom: 0.6rem;
    }

    .sidebar-title {
        text-align: center;
        text-decoration: underline;
        font-size: 24px;
        font-weight: 700;
        margin-top: 10px;
        margin-bottom: 20px;
        color: #1f2a44;
    }
    </style>
    """), unsafe_allow_html=True)


def sidebar(active_page: str):
    apply_global_styles()

    with st.sidebar:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            logo = Image.open("assets/carrefour_logo.png")
            st.image(logo, width=140)

        st.markdown('<div class="sidebar-title">Navigation</div>', unsafe_allow_html=True)

        if active_page == "Accueil":
            st.markdown('<div class="active-link">Accueil</div>', unsafe_allow_html=True)
        else:
            if st.button("Accueil"):
                st.switch_page("app.py")

        if active_page == "Vue":
            st.markdown('<div class="active-link">Vue d\'ensemble</div>', unsafe_allow_html=True)
        else:
            if st.button("Vue d'ensemble"):
                st.switch_page("pages/1_Accueil.py")

        if active_page == "RFM":
            st.markdown('<div class="active-link">Segmentation RFM</div>', unsafe_allow_html=True)
        else:
            if st.button("Segmentation RFM"):
                st.switch_page("pages/2_Segmentation.py")

        if active_page == "Recherche":
            st.markdown('<div class="active-link">Recherche</div>', unsafe_allow_html=True)
        else:
            if st.button("Recherche"):
                st.switch_page("pages/3_Recherche.py")