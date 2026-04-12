import streamlit as st
from utils.sidebar import sidebar

st.set_page_config(
    page_title="DataMarket Carrefour",
    layout="wide",
    initial_sidebar_state="expanded"
)

sidebar("Accueil")

st.markdown('<div class="title">DataMarket Carrefour</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Application d’analyse des données clients</div>',
    unsafe_allow_html=True
)

st.divider()

st.html("""
<div class="main-box">

    <div class="center-text">
        Bienvenue dans l’application <b>DataMarket Carrefour</b>.<br><br>
        Cette application permet d’explorer les données clients et les transactions afin
        d’analyser les comportements d’achat et d’identifier différents segments de clients.
    </div>

    <br>

    <div class="small-note">
        Utilisez le menu de navigation pour accéder aux différentes analyses.
    </div>

</div>
""")